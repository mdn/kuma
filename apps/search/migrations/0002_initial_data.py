# -*- coding: utf-8 -*-
from south.v2 import DataMigration

# the format for those filters is (<group>, ((<name>, <tags>, <slug>), ..))
filters = (
    ('Topics', (
        ('Open Web Apps', 'Apps', 'apps'),
        ('HTML', 'HTML', 'html'),
        ('CSS', 'CSS', 'css'),
        ('JavaScript', 'JavaScript', 'js'),
        ('APIs and DOM', 'API', 'api'),
        ('Canvas', 'Canvas', 'canvas'),
        ('SVG', 'SVG', 'svg'),
        ('MathML', 'MathML', 'mathml'),
        ('WebGL', 'WebGL', 'webgl'),
        ('XUL', 'XUL', 'xul'),
        ('Marketplace', 'Marketplace', 'marketplace'),
        ('Firefox', 'Firefox', 'firefox'),
        ('Firefox for Android', 'Firefox Mobile', 'firefox-mobile'),
        ('Firefox for Desktop', 'Firefox Desktop', 'firefox-desktop'),
        ('Firefox OS', 'Firefox OS', 'firefox-os'),
        ('Mobile', 'Mobile', 'mobile'),
        ('Web Development', '"Web Development"', 'webdev'),
        ('Add-ons & Extensions',
         ['Add-ons', 'Extensions', 'Plugins', 'Themes'],
         'addons'),
        ('Games', 'Games', 'games'),
    )),
    ('Skill level', (
        ("I'm an Expert", 'Advanced', 'advanced'),
        ('Intermediate', 'Intermediate', 'intermediate'),
        ("I'm Learning", 'Beginner', 'beginner'),
    )),
    ('Document type', (
        ('Tools', 'Tools', 'tools'),
        ('Code Samples', 'Example', 'code'),
        ('How-To & Tutorial', 'Guide', 'howto'),
    )),
)


class Migration(DataMigration):

    depends_on = (
        ("taggit", "0002_auto"),
    )

    def forwards(self, orm):
        ContentType = orm['contenttypes.contenttype']
        Tag = orm['taggit.tag']
        TaggedItem = orm['taggit.taggeditem']
        filter_ct, filter_ct_created = ContentType.objects.get_or_create(
            app_label='search',
            model='filter', defaults={'name': 'search filter'}
        )

        for group_name, filter_list in filters:
            filter_group = orm.FilterGroup.objects.create(name=group_name)

            for filter_name, filter_tags, slug in filter_list:
                if not isinstance(filter_tags, (list, tuple)):
                    filter_tags = (filter_tags,)

                filter_, created = orm.Filter.objects.get_or_create(
                    group=filter_group, name=filter_name, slug=slug)

                for tag_name in filter_tags:
                    tag, created = Tag.objects.get_or_create(name=tag_name,
                                                             slug=tag_name)
                    tagged_item, created = TaggedItem.objects.get_or_create(
                        tag=tag, content_type=filter_ct, object_id=filter_.id)

    def backwards(self, orm):
        "Write your backwards methods here."

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
            'group': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'filters'", 'to': "orm['search.FilterGroup']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'search.filtergroup': {
            'Meta': {'object_name': 'FilterGroup'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '255'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        }
    }

    complete_apps = ['taggit', 'search']
    symmetrical = True
