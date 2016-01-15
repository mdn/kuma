# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


REMOVE_DEMOS = [
    # Remove the tag tracker rows for all demos.
    # Note: This doesn't remove the tags themselves. This can be cleaned up another time.
    ('DELETE taggit_taggeditem FROM taggit_taggeditem '
     'JOIN django_content_type ON taggit_taggeditem.content_type_id=django_content_type.id '
     'WHERE django_content_type.app_label=%s', ['demos']),

    # The tagging_* tables were only used by demos and can be removed.
    ('DROP TABLE IF EXISTS tagging_tag', None),
    ('DROP TABLE IF EXISTS tagging_taggeditem', None),

    # Clean up Django's permissions.
    ('DELETE auth_permission FROM auth_permission '
     'JOIN django_content_type ON auth_permission.content_type_id=django_content_type.id '
     'WHERE django_content_type.app_label IN (%s, %s, %s)', ['demos', 'contentflagging', 'actioncounters']),

    # Drop all tables from models removed with code.
    ('DROP TABLE IF EXISTS demos_submission', None),
    ('DROP TABLE IF EXISTS contentflagging_contentflag', None),
    ('DROP TABLE IF EXISTS actioncounters_actioncounterunique', None),
    ('DROP TABLE IF EXISTS actioncounters_testmodel', None),
]


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0001_initial'),
    ]

    operations = [
        migrations.RunSQL(REMOVE_DEMOS),
    ]
