# -*- coding: utf-8 -*-
"""
Manually schedule the rendering of a document
"""
from __future__ import division

import datetime
import logging
from math import ceil
from optparse import make_option

from celery import chain

from django.core.management.base import BaseCommand, CommandError
from django.db.models import Q

from kuma.core.utils import chunked
from kuma.wiki.helpers import absolutify
from kuma.wiki.models import Document, DocumentRenderingInProgress
from kuma.wiki.tasks import (email_render_document_progress, render_document,
                             render_document_chunk)


log = logging.getLogger('kuma.wiki.management.commands.render_document')


class Command(BaseCommand):
    args = '<document_path document_path ...>'
    help = 'Render a wiki document'
    option_list = BaseCommand.option_list + (
        make_option('--all', dest='all', default=False, action='store_true',
                    help='Render ALL documents'),
        make_option('--min-age', dest='min_age', type='int', default=600,
                    help='Documents rendered less than this many seconds ago '
                         'will be skipped'),
        make_option('--baseurl', dest='baseurl', default=False,
                    help='Base URL to site'),
        make_option('--force', action='store_true', dest='force',
                    default=False,
                    help='Force rendering, first clearing record of any '
                         'rendering in progress'),
        make_option('--nocache', action='store_true', dest='nocache',
                    default=False,
                    help='Use Cache-Control: no-cache instead of max-age=0'),
        make_option('--defer', action='store_true', dest='defer',
                    default=False,
                    help='Defer rendering by chaining tasks via celery'),
    )

    def handle(self, *args, **options):
        self.options = options
        self.base_url = options['baseurl'] or absolutify('')
        if self.options['nocache']:
            self.cache_control = 'no-cache'
        else:
            self.cache_control = 'max-age=0'

        if options['all']:
            # Query all documents, excluding those whose `last_rendered_at` is
            # within `min_render_age` or NULL.
            min_render_age = (
                datetime.datetime.now() -
                datetime.timedelta(seconds=self.options['min_age']))
            docs = Document.objects.filter(
                Q(last_rendered_at__isnull=True) |
                Q(last_rendered_at__lt=min_render_age))
            docs = docs.order_by('-modified')
            docs = docs.values_list('id', flat=True)

            self.chain_render_docs(docs)

        else:
            if not len(args) == 1:
                raise CommandError('Need at least one document path to render')
            for path in args:
                # Accept a single page path from command line, but be liberal
                # in what we accept, eg: /en-US/docs/CSS (full path);
                # /en-US/CSS (no /docs); or even en-US/CSS (no leading slash)
                if path.startswith('/'):
                    path = path[1:]
                locale, sep, slug = path.partition('/')
                head, sep, tail = slug.partition('/')
                if head == 'docs':
                    slug = tail
                doc = Document.objects.get(locale=locale, slug=slug)
                log.info(u'Rendering %s (%s)' % (doc, doc.get_absolute_url()))
                try:
                    render_document(doc.pk, self.cache_control, self.base_url,
                                    self.options['force'])
                    log.debug(u'DONE.')
                except DocumentRenderingInProgress:
                    log.error(
                        u'Rendering is already in progress for this document.')

    def chain_render_docs(self, docs):
        tasks = []
        count = 0
        total = len(docs)
        n = int(ceil(total / 5))
        chunks = chunked(docs, n)

        for chunk in chunks:
            count += len(chunk)
            tasks.append(
                render_document_chunk.si(chunk, self.cache_control,
                                         self.base_url, self.options['force']))
            percent_complete = int(ceil((count / total) * 100))
            tasks.append(
                email_render_document_progress.si(percent_complete, total))

        # Make it so.
        chain(*tasks).apply_async()
