# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0003_auto_20150703_0419'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='team',
        ),
    ]
