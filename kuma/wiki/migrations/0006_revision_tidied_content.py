# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0005_delete_teamwork_contenttypes'),
    ]

    operations = [
        migrations.AddField(
            model_name='revision',
            name='tidied_content',
            field=models.TextField(blank=True),
            preserve_default=True,
        ),
    ]
