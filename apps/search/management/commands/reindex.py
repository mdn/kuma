from optparse import make_option

from django.core.management.base import BaseCommand

from search.utils import reindex


class Command(BaseCommand):
    help = 'Reindex the database for Sphinx.'
    option_list = BaseCommand.option_list + (
        make_option('--rotate', dest='rotate', action='store_true',
                    default=False, help='Rotate indexes for running server.'),
    )

    def handle(self, *args, **options):
        reindex(options['rotate'])
