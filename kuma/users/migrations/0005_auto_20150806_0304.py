# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0004_auto_20150722_1243'),
    ]

    operations = [
        migrations.DeleteModel(
            name='UserProfile',
        ),
    ]
