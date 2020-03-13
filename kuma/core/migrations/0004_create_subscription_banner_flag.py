# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def create_subscription_banner_flag(apps, schema_editor):
    Flag = apps.get_model("waffle", "Flag")
    if not Flag.objects.filter(name="subscription_banner").exists():
        Flag.objects.create(
            name="subscription_banner", staff=True, note="Shows the subscription banner"
        )


class Migration(migrations.Migration):

    dependencies = [
        ("core", "0003_auto_20191212_0638"),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ("waffle", "0001_initial"),
    ]

    operations = [migrations.RunPython(create_subscription_banner_flag)]
