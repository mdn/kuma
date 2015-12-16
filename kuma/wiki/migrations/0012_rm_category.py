# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0011_create_spam_data'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='document',
            name='category',
        ),
    ]
