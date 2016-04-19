# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0030_add_page_creators_group'),
    ]

    operations = [
        migrations.AddField(
            model_name='revisionip',
            name='data',
            field=models.TextField(verbose_name='Data submitted to Akismet', null=True, editable=False, blank=True),
        ),
    ]
