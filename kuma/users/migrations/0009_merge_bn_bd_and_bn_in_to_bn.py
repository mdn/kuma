# -*- coding: utf-8 -*-
# Generated by Django 1.11.23 on 2019-09-11 09:37
from __future__ import unicode_literals

from django.db import migrations


def change_locale_bn_bd_and_bn_in_to_bn_forwards(apps, schema_editor):
    User = apps.get_model('users', 'User')

    # Change bn-BD profile to bn
    User.objects.all().filter(locale='bn-BD').update(locale='bn')
    # Change bn-IN profile to bn
    User.objects.all().filter(locale='bn-IN').update(locale='bn')


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0008_auto_20190610_0822'),
    ]

    operations = [
        migrations.RunPython(change_locale_bn_bd_and_bn_in_to_bn_forwards)
    ]
