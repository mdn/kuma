# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_developer_needs_banner_flag(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    if not Flag.objects.filter(name="developer_needs").exists():
        Flag.objects.create(
            name="developer_needs",
            staff=True,
            note="Shows the MDN developer needs survey banner",
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0009_remove_user_interviews_banner_flag"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_developer_needs_banner_flag)]
