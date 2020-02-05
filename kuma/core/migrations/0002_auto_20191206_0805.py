# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-12-06 08:05
from __future__ import unicode_literals

from django.db import migrations


def move_developer_needs_flag_to_switch(apps, schema_editor):
    Flag = apps.get_model('waffle', 'Flag')
    Switch = apps.get_model('waffle', 'Switch')
    name = 'developer_needs'
    for flag in Flag.objects.filter(name=name):
        active = flag.everyone or (flag.percent and flag.percent > 0)
        Switch.objects.get_or_create(name=name, active=active, note=flag.note)
        flag.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_squashed_0004_remove_unused_tags'),
        # This is needed otherwise `apps.get_model('waffle', 'Flag')`
        # will raise a Django app LookupError.
        ('waffle', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(move_developer_needs_flag_to_switch)
    ]
