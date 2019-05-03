# -*- coding: utf-8 -*-
# Generated by Django 1.11.20 on 2019-04-29 11:50
from __future__ import unicode_literals

from django.db import migrations

def purge_all_deleted_document(apps, schema_editor):
    Document = apps.get_model('wiki', 'Document')
    for document in Document.objects.filter(deleted=True):
        document.delete()


class Migration(migrations.Migration):

    dependencies = [
        ('wiki', '0002_remove_document_zone'),
    ]

    operations = [
        # Purge all document that are soft deleted
        migrations.RunPython(purge_all_deleted_document),
        # Remove restore and purge permissions
        migrations.AlterModelOptions(
            name='document',
            options={'permissions': (('view_document', 'Can view document'), ('move_tree', 'Can move a tree of documents'))},
        ),
        # Remove soft deletion field (tombstone)
        migrations.RemoveField(
            model_name='document',
            name='deleted',
        ),
    ]