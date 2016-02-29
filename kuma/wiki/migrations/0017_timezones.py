# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.utils.timezone
import django_extensions.db.fields


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0016_extend_revision_ip'),
    ]

    operations = [
        migrations.AlterField(
            model_name='revision',
            name='created',
            field=models.DateTimeField(default=django.utils.timezone.now, db_index=True),
        ),
    ]
