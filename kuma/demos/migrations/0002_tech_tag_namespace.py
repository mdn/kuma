# encoding: utf-8
import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from taggit.utils import edit_string_for_tags, parse_tags
from taggit.models import TaggedItem, GenericTaggedItemBase
from taggit.managers import _TaggableManager

class Migration(DataMigration):

    KNOWN_TECH_TAGS = (
        "audio", "canvas", "css3", "device", "files", "fonts", "forms",
        "geolocation", "javascript", "html5", "indexeddb", "dragndrop",
        "mobile", "offlinesupport", "svg", "video", "webgl", "websockets",
        "webworkers", "xhr", "multitouch",
    )

    def forwards(self, orm):
        "Convert from django-tagging tags to tech:* tags under django-taggit"
        for demo in orm.Submission.objects.all():
            tags = parse_tags(demo.tags)
            # HACK: South gets confused by taggit_tags field, so we have to conjure it up here
            taggit_tags = _TaggableManager(through=TaggedItem, model=orm.Submission, instance=demo)
            taggit_tags.set(*(
                'tech:%s' % ( x )
                for x in tags
                if x in self.KNOWN_TECH_TAGS
            ))
            # Could destroy the data, but why bother?
            # demo.tags = ''
            demo.save()

    def backwards(self, orm):
        "Convert back from tech:* tags under django-taggit to django-tagging tags"
        for demo in orm.Submission.objects.all():
            # HACK: South gets confused by taggit_tags field, so we have to conjure it up here
            taggit_tags = _TaggableManager(through=TaggedItem, model=orm.Submission, instance=demo)
            demo.tags = ' '.join(
                x.name.replace('tech:', '')
                for x in taggit_tags.all()
                if (x.name.startswith('tech:'))
            )
            # Could destroy the data, but why bother?
            # taggit_tags.clear()
            demo.save()

    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'demos.submission': {
            'Meta': {'object_name': 'Submission'},
            'censored': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'comments_total': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True'}),
            'demo_package': ('kuma.demos.models.ReplacingZipFileField', [], {'max_upload_size': '62914560', 'max_length': '255'}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'featured': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'hidden': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'launches_recent': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True', 'blank': 'True'}),
            'launches_total': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True', 'blank': 'True'}),
            'license_name': ('django.db.models.fields.CharField', [], {'max_length': '64'}),
            'likes_recent': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True', 'blank': 'True'}),
            'likes_total': ('django.db.models.fields.IntegerField', [], {'default': '0', 'db_index': 'True', 'blank': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'navbar_optout': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'screenshot_1': ('kuma.demos.models.ReplacingImageWithThumbField', [], {'max_length': '255'}),
            'screenshot_2': ('kuma.demos.models.ReplacingImageWithThumbField', [], {'max_length': '255', 'blank': 'True'}),
            'screenshot_3': ('kuma.demos.models.ReplacingImageWithThumbField', [], {'max_length': '255', 'blank': 'True'}),
            'screenshot_4': ('kuma.demos.models.ReplacingImageWithThumbField', [], {'max_length': '255', 'blank': 'True'}),
            'screenshot_5': ('kuma.demos.models.ReplacingImageWithThumbField', [], {'max_length': '255', 'blank': 'True'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50', 'db_index': 'True'}),
            'source_code_url': ('django.db.models.fields.URLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'summary': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            # HACK: This custom field has gone away entirely, so using its
            # superclass as a stand-in
            #'tags': ('kuma.demos.models.ConstrainedTagField', [], {}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'video_url': ('kuma.demos.embed.VideoEmbedURLField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'})
        }
    }

    complete_apps = ['demos']
