# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0032_alt-zone-css'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='documentzone',
            name='styles',
        ),
    ]
