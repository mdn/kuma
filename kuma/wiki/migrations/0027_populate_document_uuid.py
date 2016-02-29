# -*- coding: utf-8 -*-
from __future__ import unicode_literals
from uuid import uuid4

from django.db import migrations


def populate_uuids(apps, schema_editor):
    """Populate Document.uuid, without bumping last modified."""
    Document = apps.get_model('wiki', 'Document')
    docs = Document.objects.filter(uuid__isnull=True)
    for document_id in docs.values_list('id', flat=True).iterator():
        Document.objects.filter(id=document_id).update(uuid=uuid4())


def clear_uuids(apps, schema_editor):
    """Clear Document.uuid."""
    Document = apps.get_model('wiki', 'Document')
    Document.objects.exclude(uuid__isnull=True).update(uuid=None)


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0026_document_uuid_default'),
    ]

    operations = [
        migrations.RunPython(populate_uuids, clear_uuids)
    ]
