# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def remove_l10n_survey_banner_flag(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    Flag.objects.filter(name="l10n_survey").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0007_create_user_interviews_banner_flag"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(remove_l10n_survey_banner_flag)]
