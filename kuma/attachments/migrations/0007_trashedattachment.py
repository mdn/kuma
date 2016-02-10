# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import kuma.attachments.utils


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0006_auto_20160204_1516'),
    ]

    operations = [
        migrations.CreateModel(
            name='TrashedAttachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(help_text='The attachment file that was trashed', max_length=500, upload_to=kuma.attachments.utils.attachment_upload_to)),
                ('trashed_at', models.DateTimeField(default=datetime.datetime.now, help_text='The date and time the attachment was trashed')),
                ('trashed_by', models.CharField(help_text='The username of the user who trashed the attachment', max_length=30, blank=True)),
                ('was_current', models.BooleanField(default=False, help_text='Whether or not this attachment was the current attachment revision at the time of trashing.')),
            ],
            options={
                'verbose_name': 'Trashed attachment',
                'verbose_name_plural': 'Trashed attachments',
            },
        ),
    ]
