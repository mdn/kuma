# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_user_interviews_banner_flag(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    if not Flag.objects.filter(name="user_interviews").exists():
        Flag.objects.create(
            name="user_interviews",
            staff=True,
            note="Shows the user interviews invitation banner",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0006_create_l10n_survey_banner_flag"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_user_interviews_banner_flag)]
