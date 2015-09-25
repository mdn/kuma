# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0013_remove_helpfulvote'),
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
        migrations.AddField(
            model_name='revision',
            name='localization_in_progress',
            field=models.BooleanField(default=False, help_text=b'Localization in progress', db_index=True),
            preserve_default=True,
        ),
    ]
