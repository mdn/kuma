# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def remove_browser_compat_report_banner_switch(apps, schema_editor):
    Switch = apps.get_model("waffle", "Switch")
    Switch.objects.filter(name="mdn_browser_compat_report").delete()


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0010_create_browser_compat_report_banner_switch"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(remove_browser_compat_report_banner_switch)]
