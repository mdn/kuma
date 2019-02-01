"""
Delete old DocumentSpamAttempt data
"""
from __future__ import unicode_literals

from django.core.management.base import BaseCommand

from kuma.wiki.tasks import delete_old_documentspamattempt_data


class Command(BaseCommand):
    help = "Delete old DocumentSpamAttempt.data"

    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            help="How many days 'old' (default 30)",
            default=30,
            type=int)

    def handle(self, *args, **options):
        delete_old_documentspamattempt_data(days=options['days'])
