# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0002_auto_20150430_0752'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='attachmentrevision',
            options={'verbose_name': 'attachment revision', 'verbose_name_plural': 'attachment revisions'},
        ),
        migrations.AlterField(
            model_name='attachment',
            name='mindtouch_attachment_id',
            field=models.IntegerField(help_text=b'ID for migrated MindTouch resource', null=True, db_index=True, blank=True),
        ),
        migrations.AlterField(
            model_name='attachmentrevision',
            name='mindtouch_old_id',
            field=models.IntegerField(help_text=b'ID for migrated MindTouch resource revision', unique=True, null=True, db_index=True, blank=True),
        ),
    ]
