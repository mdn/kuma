# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging
from django.db import migrations

logger = logging.getLogger(__name__)


document_columns = [
    ('html', 'NOT NULL'),
    ('rendered_html', ''),
    ('rendered_errors', ''),
    ('json', ''),
    ('body_html', ''),
    ('quick_links_html', ''),
    ('zone_subnav_local_html', ''),
    ('toc_html', ''),
    ('summary_html', ''),
    ('summary_text', ''),
]

revision_columns = [
    ('summary', 'NOT NULL'),
    ('content', 'NOT NULL'),
    ('tidied_content', 'NOT NULL'),
]


def alter_columns(cursor, table, columns, charset, collation):
    for column, extra in columns:
        logger.debug('Altering column %s of table %s', column, table)
        query = ('ALTER TABLE %s '
                 'CHANGE %s %s LONGTEXT '
                 'CHARACTER SET %s '
                 'COLLATE %s '
                 '%s;' %
                 (table, column, column, charset, collation, extra))
        logger.debug('Running query %s', query)
        cursor.execute(query)


def forwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        alter_columns(cursor, 'wiki_document', document_columns,
                      'utf8mb4', 'utf8mb4_unicode_ci')
        alter_columns(cursor, 'wiki_revision', revision_columns,
                      'utf8mb4', 'utf8mb4_unicode_ci')


def backwards(apps, schema_editor):
    with schema_editor.connection.cursor() as cursor:
        alter_columns(cursor, 'wiki_document', document_columns,
                      'utf8', 'utf8_unicode_ci')
        alter_columns(cursor, 'wiki_revision', revision_columns,
                      'utf8', 'utf8_unicode_ci')


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0006_revision_tidied_content'),
    ]

    operations = [migrations.RunPython(forwards, backwards)]
