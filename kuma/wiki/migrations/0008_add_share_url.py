# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0007_update_locale_fields'),
    ]

    operations = [
        migrations.AddField(
            model_name='document',
            name='share_url',
            field=models.URLField(null=True, blank=True),
            preserve_default=True,
        ),
    ]
