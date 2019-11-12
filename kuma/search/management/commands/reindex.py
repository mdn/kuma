import logging

from django.core.management.base import BaseCommand, CommandError

from kuma.wiki.search import WikiDocumentType


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'

    def add_arguments(self, parser):
        parser.add_argument(
            '-c', '--chunk',
            help='Chunk size when reindexing (default 250). Lower is better'
                 'for slow computers with little memory',
            type=int,
            dest='chunk_size',
            default=250)
        parser.add_argument(
            '-p', '--percent',
            help='the percentage of the db to index (1 to 100) (default 100)',
            type=int,
            default=100)

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)

        percent = options['percent']
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')

        message = WikiDocumentType.reindex_all(options['chunk_size'],
                                               percent=percent)
        self.stdout.write(message + '\n')
