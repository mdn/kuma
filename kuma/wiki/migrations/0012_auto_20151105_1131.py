# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0011_create_spam_data'),
    ]

    operations = [
        migrations.AlterField(
            model_name='documentspamattempt',
            name='document',
            field=models.ForeignKey(related_name='spam_attempts', on_delete=django.db.models.deletion.SET_NULL, verbose_name=b'Document (optional)', blank=True, to='wiki.Document', null=True),
            preserve_default=True,
        ),
    ]
