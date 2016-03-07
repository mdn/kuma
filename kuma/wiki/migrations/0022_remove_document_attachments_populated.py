# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0021_document_attachments_populated'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='attachments_populated',
        ),
    ]
