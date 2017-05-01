# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import taggit.managers


class Migration(migrations.Migration):

    dependencies = [
        ('search', '0002_filter_default'),
    ]

    operations = [
        migrations.AlterField(
            model_name='filter',
            name='tags',
            field=taggit.managers.TaggableManager(to='taggit.Tag', through='taggit.TaggedItem', help_text=b'A comma-separated list of tags. If more than one tag given the operator specified is used', verbose_name='Tags'),
        ),
    ]
