# -*- coding: utf-8 -*-
from south.v2 import DataMigration
from django.template.defaultfilters import slugify


class Migration(DataMigration):

    def get_tags(self, orm):
        ContentType = orm['contenttypes.ContentType']
        filter_ct = ContentType.objects.get(app_label='search', model='filter')
        return orm['taggit.Tag'].objects.filter(
            taggit_taggeditem_items__content_type=filter_ct.pk)

    def forwards(self, orm):
        for tag in self.get_tags(orm):
            tag.slug = slugify(tag.slug)
            tag.save()

        # Fixing a mistake in the initial data of search filter tags, d'oh!
        webdev_tag = orm['taggit.Tag'].objects.filter(name='"Web Development"')[0]
        webdev_tag.name = "Web Development"
        webdev_tag.save()

    def backwards(self, orm):
        for tag in self.get_tags(orm):
            tag.slug = tag.name
            tag.save()
        webdev_tag = orm['taggit.Tag'].objects.filter(name='Web Development')[0]
        webdev_tag.name = '"Web Development"'
        webdev_tag.save()

    models = {
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'search.filter': {
            'Meta': {'unique_together': "(('name', 'slug'),)", 'object_name': 'Filter'},
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'filters'", 'to': "orm['search.FilterGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'operator': ('django.db.models.fields.CharField', [], {'default': "'OR'", 'max_length': '3'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'search.filtergroup': {
            'Meta': {'ordering': "('-order', 'name')", 'object_name': 'FilterGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'order': ('django.db.models.fields.IntegerField', [], {'default': '1'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "u'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['search']
    symmetrical = True
