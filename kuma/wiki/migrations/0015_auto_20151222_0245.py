# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def set_localization_in_progress(apps, schema_editor):
    LocalizationTag = apps.get_model('wiki', 'LocalizationTag')
    inprogress_tag = LocalizationTag.objects.filter(name='inprogress')
    revision_pks = (inprogress_tag.wiki_localizationtaggedrevision_items
                                  .values_list('content_object__pk', flat=True))
    inprogress_revisions = Revision.objects.filter(pk__in=revision_pks)
    inprogress_revisions.update(localization_in_progress=True)


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0014_auto_20150924_1713'),
    ]

    operations = [
        migrations.RunPython(set_localization_in_progress),
    ]
