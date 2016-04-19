# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import datetime
import kuma.attachments.utils
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Attachment',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('title', models.CharField(max_length=255, db_index=True)),
                ('slug', models.CharField(max_length=255, db_index=True)),
                ('mindtouch_attachment_id', models.IntegerField(help_text=b'ID for migrated MindTouch resource', null=True, db_index=True)),
                ('modified', models.DateTimeField(db_index=True, auto_now=True, null=True)),
            ],
            options={
                'permissions': (('disallow_add_attachment', 'Cannot upload attachment'),),
            },
        ),
        migrations.CreateModel(
            name='AttachmentRevision',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', models.FileField(max_length=500, upload_to=kuma.attachments.utils.attachment_upload_to)),
                ('title', models.CharField(max_length=255, null=True, db_index=True)),
                ('slug', models.CharField(max_length=255, null=True, db_index=True)),
                ('mime_type', models.CharField(max_length=255, db_index=True)),
                ('description', models.TextField(blank=True)),
                ('created', models.DateTimeField(default=datetime.datetime.now)),
                ('comment', models.CharField(max_length=255, blank=True)),
                ('is_approved', models.BooleanField(default=True, db_index=True)),
                ('mindtouch_old_id', models.IntegerField(help_text=b'ID for migrated MindTouch resource revision', unique=True, null=True, db_index=True)),
                ('is_mindtouch_migration', models.BooleanField(default=False, help_text=b'Did this revision come from MindTouch?', db_index=True)),
                ('attachment', models.ForeignKey(related_name='revisions', to='attachments.Attachment')),
                ('creator', models.ForeignKey(related_name='created_attachment_revisions', to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.AddField(
            model_name='attachment',
            name='current_revision',
            field=models.ForeignKey(related_name='current_rev', to='attachments.AttachmentRevision', null=True),
        ),
    ]
