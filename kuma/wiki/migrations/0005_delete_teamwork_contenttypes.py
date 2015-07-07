# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations

def remove_content_type(apps, schema_editor):
    ContentType = apps.get_model('contenttypes', 'ContentType')
    db_alias = schema_editor.connection.alias
    ContentType.objects.using(db_alias).filter(app_label='teamwork').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0004_remove_document_team'),
    ]

    operations = [
        migrations.RunPython(
            remove_content_type,
        ),
    ]
