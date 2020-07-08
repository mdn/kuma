# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_l10n_survey_banner_flag(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    if not Flag.objects.filter(name="l10n_survey").exists():
        Flag.objects.create(
            name="l10n_survey", staff=True, note="Shows the l10n survey banner"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0005_auto_20200409_1312"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_l10n_survey_banner_flag)]
