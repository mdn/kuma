import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from kuma.wiki.search import WikiDocumentType


class Command(BaseCommand):
    help = 'Reindex the database for Elastic.'
    option_list = BaseCommand.option_list + (
        make_option('-c', '--chunk', type='int', dest='chunk_size', default=1000,
                    help='Chunk size when reindexing. Lower is better for '
                         'slow computers with little memory'),
        make_option('-p', '--percent', type='int', dest='percent', default=100,
                    help='the percentage of the db to index (1 to 100)'),
    )

    def handle(self, *args, **options):
        logging.basicConfig(level=logging.INFO)

        percent = options['percent']
        if not 1 <= percent <= 100:
            raise CommandError('percent should be between 1 and 100')

        message = WikiDocumentType.reindex_all(options['chunk_size'],
                                               percent=percent)
        self.stdout.write(unicode(message) + '\n')
