"""
Delete old revision IPs
"""
from optparse import make_option

from django.core.management.base import BaseCommand
from kuma.wiki.tasks import delete_old_revision_ips


class Command(BaseCommand):
    help = "Delete old Revision IPs"
    option_list = BaseCommand.option_list + (
        make_option('--days', dest="days", default=30, type=int,
                    help="How many days 'old'"),
    )

    def handle(self, *args, **options):
        self.options = options
        delete_old_revision_ips(days=options['days'])
