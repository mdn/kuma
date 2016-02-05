# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0020_add_is_linked_is_original'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='attachments_populated',
            field=models.BooleanField(default=False),
        ),
    ]
