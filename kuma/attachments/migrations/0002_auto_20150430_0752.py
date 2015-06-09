# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('attachments', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='attachmentrevision',
            name='creator',
            field=models.ForeignKey(related_name='created_attachment_revisions', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
        migrations.AddField(
            model_name='attachment',
            name='current_revision',
            field=models.ForeignKey(related_name='current_rev', to='attachments.AttachmentRevision', null=True),
            preserve_default=True,
        ),
    ]
