# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0019_rename_documentattachment_related_name'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentattachment',
            name='is_linked',
            field=models.BooleanField(default=False, verbose_name='linked in the document content'),
        ),
        migrations.AddField(
            model_name='documentattachment',
            name='is_original',
            field=models.BooleanField(default=False, verbose_name='uploaded to the document'),
        ),
    ]
