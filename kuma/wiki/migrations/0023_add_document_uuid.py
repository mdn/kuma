# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0022_remove_document_attachments_populated'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='uuid',
            field=models.UUIDField(default=None, null=True, editable=False),
        ),
    ]
