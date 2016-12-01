# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

def remove_unused_tags(apps, schema_editor):
    TaggedItem = apps.get_model('taggit', 'TaggedItem')
    Tag = apps.get_model('taggit', 'Tag')

    tags_content = TaggedItem.objects.all().values_list("tag__id", flat=True)
    # Delete all the tags that does not have any content associate with them
    Tag.objects.all().exclude(id__in=tags_content).delete()

class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_unused_taggeditems'),
    ]

    operations = [
        migrations.RunPython(remove_unused_tags)
    ]
