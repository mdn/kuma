# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0006_stackoverflow_validator'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='is_github_url_public',
            field=models.BooleanField(default=False, verbose_name='Public Github URL'),
        ),
    ]
