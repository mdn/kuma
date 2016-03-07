# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0003_auto_20160126_0210'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='current_revision',
            field=models.ForeignKey(related_name='current_for+', blank=True, to='attachments.AttachmentRevision', null=True),
        ),
        migrations.AlterField(
            model_name='attachmentrevision',
            name='mime_type',
            field=models.CharField(default=b'application/octet-stream', max_length=255, db_index=True),
        ),
    ]
