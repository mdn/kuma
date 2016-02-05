# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0004_auto_20160204_1248'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachmentrevision',
            name='mime_type',
            field=models.CharField(default=b'application/octet-stream', help_text='The MIME type is used when serving the attachment. Automatically populated by inspecting the file on upload. Please only override if needed.', max_length=255, db_index=True, blank=True),
        ),
    ]
