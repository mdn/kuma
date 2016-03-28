# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='filter',
            name='default',
            field=models.BooleanField(default=False, help_text=b'Whether this filter is applied in the absence of a user-chosen filter'),
        ),
    ]
