# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0012_rm_category'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='helpfulvote',
            name='creator',
        ),
        migrations.RemoveField(
            model_name='helpfulvote',
            name='document',
        ),
        migrations.DeleteModel(
            name='HelpfulVote',
        ),
    ]
