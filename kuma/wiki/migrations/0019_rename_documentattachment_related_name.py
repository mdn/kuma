# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0018_update_locale_fields'),
    ]

    operations = [

        migrations.AlterField(
            model_name='documentattachment',
            name='document',
            field=models.ForeignKey(related_name='attached_files', to='wiki.Document'),
        ),
        migrations.AlterField(
            model_name='documentattachment',
            name='file',
            field=models.ForeignKey(related_name='document_attachments', to='attachments.Attachment'),
        ),
    ]
