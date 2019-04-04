# -*- coding: utf-8 -*-
"""
Manually schedule the publishing of one or more documents to the API.
"""
from __future__ import unicode_literals

from collections import namedtuple

from celery.canvas import chord
from django.core.management.base import BaseCommand, CommandError

from kuma.api.tasks import notify_publication, publish
from kuma.wiki.models import Document


class Command(BaseCommand):
    args = '<document_path document_path ...>'
    help = 'Publish one or more documents to the document API'

    def add_arguments(self, parser):
        parser.add_argument(
            'paths',
            help='Path to document(s), like /en-US/docs/Web',
            nargs='*',  # overridden by --all or --locale
            metavar='path')
        parser.add_argument(
            '--all',
            help='Publish ALL documents (rather than by path)',
            action='store_true')
        parser.add_argument(
            '--locale',
            help='Publish ALL documents in this locale (rather than by path)')
        parser.add_argument(
            '--chunk-size',
            type=int,
            default=100,
            help='Partition the work into tasks, with each task handling this '
                 'many documents (default=100)')

    def handle(self, *args, **options):
        Logger = namedtuple('Logger', 'info, error')
        log = Logger(info=self.stdout.write, error=self.stderr.write)
        if options['all'] or options['locale']:
            filters = {}
            if options['locale'] and not options['all']:
                locale = options['locale']
                log.info('Publishing all documents in locale {}'.format(locale))
                filters.update(locale=locale)
            else:
                locale = None
                log.info('Publishing all documents')
            docs = Document.objects.filter(**filters)
            doc_pks = docs.values_list('id', flat=True)
            log.info('...found {} documents.'.format(len(doc_pks)))
            chunk_size = max(options['chunk_size'], 1)
            chord(
                publish.chunks(((pk,) for pk in doc_pks), chunk_size).group(),
                notify_publication.si(locale=locale)
            ).apply_async()
        else:
            # Accept page paths from command line, but be liberal
            # in what we accept, eg: /en-US/docs/CSS (full path);
            # /en-US/CSS (no /docs); or even en-US/CSS (no leading slash)
            paths = options['paths']
            if not paths:
                raise CommandError('Need at least one document path to publish')
            for path in paths:
                if path.startswith('/'):
                    path = path[1:]
                locale, sep, slug = path.partition('/')
                head, sep, tail = slug.partition('/')
                if head == 'docs':
                    slug = tail
                try:
                    doc = Document.objects.get(locale=locale, slug=slug)
                except Document.DoesNotExist:
                    msg = 'Document with locale={} and slug={} does not exist'
                    raise CommandError(msg.format(locale, slug))
                publish(doc.pk, log=log, mail_admins_on_error=False)
