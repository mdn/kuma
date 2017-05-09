# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0031_add_data_to_revisionip'),
    ]

    operations = [
        migrations.AddField(
            model_name='documentzone',
            name='css_slug',
            field=models.CharField(help_text=b'name of an alternative pipeline CSS group for documents under this zone (note that "zone-" will be prepended)', max_length=100, blank=True),
        ),
    ]
