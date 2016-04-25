# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations
from django.db.models import Count
from django.core.management.sql import emit_post_migrate_signal


def create_page_creators_group(apps, schema_editor):
    # Ensure wiki.add_document permission is created in a fresh database
    # https://code.djangoproject.com/ticket/23422#comment:20
    db_alias = schema_editor.connection.alias
    emit_post_migrate_signal(verbosity=1,
                             interactive=False,
                             db=db_alias,
                             created_models=[])

    # Grab the wiki.add_document permission
    Permission = apps.get_model('auth', 'Permission')
    add_perm = Permission.objects.get(codename='add_document',
                                      content_type__app_label='wiki')

    # Create the Page Creators group, if needed
    Group = apps.get_model('auth', 'Group')
    group, created = Group.objects.get_or_create(name='Page Creators')
    group.permissions.add(add_perm)

    # Add existing unbanned users to Page Creators
    User = apps.get_model('users', 'User')
    for user in User.objects.only('id'):
        if not user.bans.exists():
            user.groups.add(group)


def delete_page_creators_group(apps, schema_editor):
    Group = apps.get_model('auth', 'Group')
    Group.objects.filter(name='Page Creators').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0029_add_dsa_review_type_error'),
        ('users', '0005_update_tz'),
        ('contenttypes', '__latest__'),
        ('sites', '__latest__'),
    ]

    operations = [
        migrations.RunPython(create_page_creators_group,
                             delete_page_creators_group),
    ]
