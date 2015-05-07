# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

from django.db import models, migrations


logger = logging.getLogger(__name__)


tables = [
    'taggit_tag',
    'wiki_documenttag',
    'wiki_localizationtag',
    'wiki_reviewtag',
]

def alter_collation(cursor, collation):
    for table in tables:
        logger.info('Altering table %s to collation %s...', table, collation)
        cursor.execute("ALTER TABLE %s "
                       "MODIFY name VARCHAR(100) "
                       "CHARACTER SET utf8 COLLATE %s;" %
                       (table, collation))


def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        alter_collation(cursor, 'utf8_distinct_ci')


def backwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        alter_collation(cursor, 'utf8_general_ci')


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0001_initial'),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
