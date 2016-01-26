# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0002_auto_20150430_0752'),
    ]

    operations = [
        migrations.AlterField(
            model_name='attachmentrevision',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
