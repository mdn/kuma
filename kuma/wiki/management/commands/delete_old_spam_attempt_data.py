"""
Delete old DocumentSpamAttempt data
"""
from optparse import make_option

from django.core.management.base import BaseCommand
from kuma.wiki.tasks import delete_old_documentspamattempt_data


class Command(BaseCommand):
    help = "Delete old DocumentSpamAttempt.data"
    option_list = BaseCommand.option_list + (
        make_option('--days', dest='days', default=30, type=int,
                    help="How many days 'old'"),
    )

    def handle(self, days, *args, **options):
        delete_old_documentspamattempt_data(days=days)
