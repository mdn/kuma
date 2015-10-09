# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0008_add_share_url'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='share_url',
        ),
    ]
