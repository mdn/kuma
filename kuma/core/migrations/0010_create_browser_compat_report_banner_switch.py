# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_browser_compat_report_banner_switch(apps, schema_editor):
    Switch = apps.get_model("waffle", "Switch")
    if not Switch.objects.filter(name="mdn_browser_compat_report").exists():
        Switch.objects.create(
            name="mdn_browser_compat_report",
            active=False,
            note="The MDN Browser Compatibility Report",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_remove_user_interviews_banner_flag"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_browser_compat_report_banner_switch)]
