# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0015_auto_20151222_0245'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='localizationtaggedrevision',
            name='content_object',
        ),
        migrations.RemoveField(
            model_name='localizationtaggedrevision',
            name='tag',
        ),
        migrations.RemoveField(
            model_name='revision',
            name='localization_tags',
        ),
        migrations.DeleteModel(
            name='LocalizationTaggedRevision',
        ),
        migrations.DeleteModel(
            name='LocalizationTag',
        ),
    ]
