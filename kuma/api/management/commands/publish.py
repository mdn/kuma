# -*- coding: utf-8 -*-
"""
Manually schedule the publishing of one or more documents to the document API.
"""


from collections import namedtuple
from math import ceil

from celery.canvas import group
from django.core.management.base import BaseCommand, CommandError

from kuma.api.tasks import publish
from kuma.core.utils import chunked
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
            default=1000,
            help='Partition the work into tasks, with each task handling this '
                 'many documents (default=1000)')
        parser.add_argument(
            '--skip-cdn-invalidation',
            help=(
                'No CDN cache invalidation after publishing. Forced to True '
                'if either the --all or --locale flag is used.'
            ),
            action='store_true')

    def handle(self, *args, **options):
        Logger = namedtuple('Logger', 'info, error')
        log = Logger(info=self.stdout.write, error=self.stderr.write)
        if options['all'] or options['locale']:
            if options['locale'] and options['all']:
                raise CommandError(
                    'Specifying --locale with --all is the same as --all'
                )
            filters = {}
            if options['locale']:
                locale = options['locale']
                log.info('Publishing all documents in locale {}'.format(locale))
                filters.update(locale=locale)
            else:
                log.info('Publishing all documents')
            chunk_size = max(options['chunk_size'], 1)
            docs = Document.objects.filter(**filters)
            doc_pks = docs.values_list('id', flat=True)
            num_docs = len(doc_pks)
            num_tasks = int(ceil(num_docs / float(chunk_size)))
            log.info('...found {} documents.'.format(num_docs))
            # Let's publish the documents in a group of chunks, where the
            # tasks in the group can be run in parallel.
            tasks = []
            for i, chunk in enumerate(chunked(doc_pks, chunk_size)):
                message = 'Published chunk #{} of {}'.format(i + 1, num_tasks)
                tasks.append(publish.si(
                    chunk,
                    completion_message=message,
                    invalidate_cdn_cache=False
                ))
            if num_tasks == 1:
                msg = ('Launching a single task handling '
                       'all {} documents.'.format(num_docs))
            else:
                msg = ('Launching {} paralellizable tasks, each handling '
                       'at most {} documents.'.format(num_tasks, chunk_size))
            log.info(msg)
            group(*tasks).apply_async()
        else:
            paths = options['paths']
            if not paths:
                raise CommandError('Need at least one document path to publish')
            doc_pks = []
            get_doc_pk = Document.objects.values_list('id', flat=True).get
            for path in paths:
                if path.startswith('/'):
                    path = path[1:]
                locale, sep, slug = path.partition('/')
                head, sep, tail = slug.partition('/')
                if head == 'docs':
                    slug = tail
                try:
                    doc_pk = get_doc_pk(locale=locale, slug=slug)
                except Document.DoesNotExist:
                    msg = 'Document with locale={} and slug={} does not exist'
                    log.error(msg.format(locale, slug))
                else:
                    doc_pks.append(doc_pk)
            publish(
                doc_pks,
                log=log,
                invalidate_cdn_cache=(not options['skip_cdn_invalidation'])
            )
