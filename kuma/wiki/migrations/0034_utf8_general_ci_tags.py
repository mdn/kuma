# -*- coding: utf-8 -*-
from __future__ import unicode_literals
import logging

logger = logging.getLogger('django.db.backends.schema')


from django.db import migrations

tags_tables = (
    ('taggit', 'Tag'),
    ('wiki', 'DocumentTag'),
    ('wiki', 'LocalizationTag'),
    ('wiki', 'ReviewTag'),
)

count_sql_pattern = (
    "SELECT id, name, COUNT(*) count"
    "  FROM %(table)s"
    "  GROUP BY name COLLATE utf8_general_ci"
    "  HAVING count > 1")

tag_sql_pattern = (
    "SELECT id, name"
    "  FROM %(table)s"
    "  WHERE name = _utf8'%(name)s' COLLATE utf8_general_ci"
    "  ORDER BY id")


def convert_tags_to_utf8_general_ci(apps, schema_editor):
    models = [apps.get_model(app, model) for app, model in tags_tables]
    for model in models:
        assert not model.objects.filter(name__endswith='(2)').exists()

    for Model in models:
        table = Model._meta.db_table
        count_sql = count_sql_pattern % {'table': table}
        named_objs = Model.objects.raw(count_sql)
        names = [obj.name for obj in named_objs]
        if names:
            logger.warn("\nUpdating tags in table %s", table)
        for name in names:
            tag_sql = tag_sql_pattern % {'table': table, 'name': name}
            tag_objs = Model.objects.raw(tag_sql)
            count = 1
            for tag in tag_objs:
                if count == 1:
                    logger.warn("  Keeping %d: '%s'", tag.id, tag.name)
                    first = False
                else:
                    old_name = tag.name
                    tag.name += '(%d)' % count
                    new_name = tag.name
                    logger.warn("  Changing %d: '%s' to '%s'", tag.id, old_name, new_name)
                    tag.save()
                count += 1


def revert_tags_to_utf8_distinct_ci(apps, schema_editor):
    models = [apps.get_model(app, model) for app, model in tags_tables]
    for Model in models:
        table = Model._meta.db_table
        count = 2
        tag_end = '(%d)' % count
        tags = Model.objects.filter(name__endswith=tag_end)
        while tags.exists():
            if count == 2:
                logger.warn("\nReverting tags in table %s", table)
            for tag in tags:
                old_name = tag.name
                tag.name = tag.name[:-len(tag_end)]
                new_name = tag.name
                logger.warn("  Reverting %d: '%s' to '%s'", tag.id, old_name, new_name)
                tag.save()
            count += 1
            tag_end = '(%d)' % count
            tags = Model.objects.filter(name__endswith=tag_end)


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0033_drop_template_perms'),
    ]

    operations = [
        migrations.RunPython(convert_tags_to_utf8_general_ci,
                             revert_tags_to_utf8_distinct_ci)
    ]
