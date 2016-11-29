# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.contrib.contenttypes.models import ContentType

def remove_taggeditem_with_no_models(apps, schema_editor):
    TaggedItem = apps.get_model('taggit', 'TaggedItem')

    tags_content_type_id = TaggedItem.objects.values_list('content_type_id', flat=True).distinct()

    for ct_id in tags_content_type_id:
        ct = ContentType.objects.get(id=ct_id)
        if ct.model_class() is None:
            TaggedItem.objects.filter(content_type_id=ct_id).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_remove_demos'),
        ('taggit', '0002_auto_20150616_2121'),
    ]

    operations = [
         migrations.RunPython(remove_taggeditem_with_no_models)
    ]
