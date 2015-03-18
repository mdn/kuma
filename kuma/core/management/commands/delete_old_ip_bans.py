"""
Delete old revision IPs
"""
from optparse import make_option

from django.core.management.base import BaseCommand
from .tasks import delete_old_ip_bans


class Command(BaseCommand):
    help = "Delete old IP Bans"
    option_list = BaseCommand.option_list + (
        make_option('--days', dest="days", default=30, type=int,
                    help="How many days 'old' (Default 30)"),
    )

    def handle(self, *args, **options):
        self.options = options
        delete_old_ip_bans(days=options['days'])
