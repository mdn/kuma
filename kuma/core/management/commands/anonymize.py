from django.db import connection
from django.core.management.base import BaseCommand
from manage import path


class Command(BaseCommand):
    help = 'Anonymize the database. Will wipe out some data.'

    def handle(self, *arg, **kwargs):
        with open(path('scripts/anonymize.sql')) as fp:
            sql = fp.read()
            cursor = connection.cursor()
            cursor.execute(sql)
