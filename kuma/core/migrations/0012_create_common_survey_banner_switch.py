# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_common_survey_banner_switch(apps, schema_editor):
    Switch = apps.get_model("waffle", "Switch")
    if not Switch.objects.filter(name="common_survey_banner").exists():
        Switch.objects.create(
            name="common_survey_banner",
            active=False,
            note="Standard MDN Web Docs Survey Baner",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0011_remove_browser_compat_report_banner_switch"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_common_survey_banner_switch)]
