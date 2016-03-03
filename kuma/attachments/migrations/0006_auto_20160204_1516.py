# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('attachments', '0005_auto_20160204_1444'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='attachment',
            name='slug',
        ),
        migrations.RemoveField(
            model_name='attachmentrevision',
            name='slug',
        ),
    ]
