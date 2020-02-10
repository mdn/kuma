import os.path

from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = "Anonymize the database. Will wipe out some data."

    def handle(self, *arg, **kwargs):
        path = os.path.join(settings.ROOT, "scripts/anonymize.sql")
        sql = open(path).read()
        assert sql
        cursor = connection.cursor()
        cursor.execute(sql)
