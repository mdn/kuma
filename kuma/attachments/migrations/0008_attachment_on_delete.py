# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0007_trashedattachment'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachment',
            name='current_revision',
            field=models.ForeignKey(related_name='current_for+', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='attachments.AttachmentRevision', null=True),
        ),
    ]
