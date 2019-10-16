# -*- coding: utf-8 -*-
"""
Manually schedule the rendering of a document
"""
from __future__ import division

import datetime
import logging
from math import ceil

from celery import chain
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from kuma.core.utils import chunked
from kuma.wiki.models import Document, DocumentRenderingInProgress
from kuma.wiki.tasks import (email_document_progress, render_document,
                             render_document_chunk)
from kuma.wiki.templatetags.jinja_helpers import absolutify


log = logging.getLogger('kuma.wiki.management.commands.render_document')


class Command(BaseCommand):
    args = '<document_path document_path ...>'
    help = 'Render a wiki document'

    def add_arguments(self, parser):
        parser.add_argument(
            'paths',
            help='Path to document(s), like /en-US/docs/Web',
            nargs='*',  # overridden by --all
            metavar='path')
        parser.add_argument(
            '--all',
            help='Render ALL documents (rather than by path)',
            action='store_true')
        parser.add_argument(
            '--locale',
            help='Publish ALL documents in this locale (rather than by path)')
        parser.add_argument(
            '--not-locale',
            help='Publish all documents NOT in this locale')
        parser.add_argument(
            '--min-age',
            help='Documents rendered less than this many seconds ago will be'
                 ' skipped (default 600)',
            type=int,
            default=600)
        parser.add_argument(
            '--baseurl',
            help='Base URL to site')
        parser.add_argument(
            '--force',
            help='Force rendering, first clearing record of any rendering in'
                 ' progress',
            action='store_true')
        parser.add_argument(
            '--nocache',
            help='Use Cache-Control: no-cache instead of max-age=0',
            action='store_true')
        parser.add_argument(
            '--skip-cdn-invalidation',
            help=(
                'No CDN cache invalidation after publishing. Forced to True '
                'if the --all flag is used.'
            ),
            action='store_true')

    def handle(self, *args, **options):
        base_url = options['baseurl'] or absolutify('')
        if options['nocache']:
            cache_control = 'no-cache'
        else:
            cache_control = 'max-age=0'
        force = options['force']
        invalidate_cdn_cache = not options['skip_cdn_invalidation']

        if options['all']:
            # Query all documents, excluding those whose `last_rendered_at` is
            # within `min_render_age` or NULL.
            min_render_age = (
                datetime.datetime.now() -
                datetime.timedelta(seconds=options['min_age']))
            docs = Document.objects.filter(
                Q(last_rendered_at__isnull=True) |
                Q(last_rendered_at__lt=min_render_age))
            if options['locale']:
                docs = docs.filter(locale=options['locale'])
            if options['not_locale']:
                docs = docs.exclude(locale=options['not_locale'])
            docs = docs.order_by('-modified')
            docs = docs.values_list('id', flat=True)

            self.chain_render_docs(
                docs,
                cache_control,
                base_url,
                force,
                invalidate_cdn_cache=invalidate_cdn_cache)

        else:
            # Accept page paths from command line, but be liberal
            # in what we accept, eg: /en-US/docs/CSS (full path);
            # /en-US/CSS (no /docs); or even en-US/CSS (no leading slash)
            paths = options['paths']
            if not paths:
                raise CommandError('Need at least one document path to render')

            for path in paths:
                if path.startswith('/'):
                    path = path[1:]
                locale, sep, slug = path.partition('/')
                head, sep, tail = slug.partition('/')
                if head == 'docs':
                    slug = tail
                doc = Document.objects.get(locale=locale, slug=slug)
                log.info(u'Rendering %s (%s)' % (doc, doc.get_absolute_url()))
                try:
                    render_document(
                        doc.pk, cache_control, base_url, force,
                        invalidate_cdn_cache=invalidate_cdn_cache
                    )
                    log.debug(u'DONE.')
                except DocumentRenderingInProgress:
                    log.error(
                        u'Rendering is already in progress for this document.')

    def chain_render_docs(self, docs, cache_control, base_url, force,
                          invalidate_cdn_cache=False):
        tasks = []
        count = 0
        total = len(docs)
        n = int(ceil(total / 5))
        chunks = chunked(docs, n)

        for chunk in chunks:
            count += len(chunk)
            tasks.append(
                render_document_chunk.si(chunk, cache_control, base_url,
                                         force, invalidate_cdn_cache))
            percent_complete = int(ceil((count / total) * 100))
            tasks.append(
                email_document_progress.si('render_document', percent_complete,
                                           total))

        # Make it so.
        chain(*tasks).apply_async()
