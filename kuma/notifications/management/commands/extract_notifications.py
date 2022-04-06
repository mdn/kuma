import json

from django.core.management.base import BaseCommand

from kuma.notifications.utils import process_changes


class Command(BaseCommand):
    help = "Extracts notifications from a changes.json file"

    def add_arguments(self, parser):
        parser.add_argument("file", type=open)

    def handle(self, *args, **options):
        changes = json.loads(options["file"].read())
        process_changes(changes)
