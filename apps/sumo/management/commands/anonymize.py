# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
