# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models
from django.utils import timezone


class Migration(SchemaMigration):

    def forwards(self, orm):

        # Adding model 'AttachmentRevision'
        db.create_table('wiki_attachmentrevision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('attachment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['attachments.Attachment'])),
            ('file', self.gf('django.db.models.fields.files.FileField')(max_length=500)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, db_index=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255, null=True, db_index=True)),
            ('mime_type', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=django.utils.timezone.now)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_attachment_revisions', to=orm['auth.User'])),
            ('is_approved', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('mindtouch_old_id', self.gf('django.db.models.fields.IntegerField')(unique=True, null=True, db_index=True)),
            ('is_mindtouch_migration', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
        ))
        db.send_create_signal('attachments', ['AttachmentRevision'])

        # Adding model 'Attachment'
        db.create_table('wiki_attachment', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('current_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='current_rev', null=True, to=orm['attachments.AttachmentRevision'])),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('mindtouch_attachment_id', self.gf('django.db.models.fields.IntegerField')(null=True, db_index=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, null=True, db_index=True, blank=True)),
        ))
        db.send_create_signal('attachments', ['Attachment'])


    def backwards(self, orm):

        # Deleting model 'AttachmentRevision'
        db.delete_table('wiki_attachmentrevision')

        # Deleting model 'Attachment'
        db.delete_table('wiki_attachment')


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
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'django.utils.timezone.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'django.utils.timezone.now'}),
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
        'attachments.attachment': {
            'Meta': {'object_name': 'Attachment', 'db_table': "'wiki_attachment'"},
            'current_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current_rev'", 'null': 'True', 'to': "orm['attachments.AttachmentRevision']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mindtouch_attachment_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'attachments.attachmentrevision': {
            'Meta': {'object_name': 'AttachmentRevision', 'db_table': "'wiki_attachmentrevision'"},
            'attachment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['attachments.Attachment']"}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'django.utils.timezone.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_attachment_revisions'", 'to': "orm['auth.User']"}),
            'description': ('django.db.models.fields.TextField', [], {'blank': 'True'}),
            'file': ('django.db.models.fields.files.FileField', [], {'max_length': '500'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_mindtouch_migration': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'mime_type': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'mindtouch_old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'})
        },
        'wiki.document': {
            'Meta': {'unique_together': "(('parent', 'locale'), ('slug', 'locale'))", 'object_name': 'Document'},
            'category': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'current_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current_for+'", 'null': 'True', 'to': "orm['wiki.Revision']"}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_localizable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_template': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'locale': ('kuma.core.fields.LocaleField', [], {'default': "'en-US'", 'max_length': '7', 'db_index': 'True'}),
            'mindtouch_page_id': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'null': 'True', 'db_index': 'True', 'blank': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'translations'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'parent_topic': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'children'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'related_documents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wiki.Document']", 'through': "orm['wiki.RelatedDocument']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
        },
        'wiki.documenttag': {
            'Meta': {'object_name': 'DocumentTag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'wiki.editortoolbar': {
            'Meta': {'object_name': 'EditorToolbar'},
            'code': ('django.db.models.fields.TextField', [], {'max_length': '2000'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_toolbars'", 'to': "orm['auth.User']"}),
            'default': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'wiki.firefoxversion': {
            'Meta': {'unique_together': "(('item_id', 'document'),)", 'object_name': 'FirefoxVersion'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'firefox_version_set'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.IntegerField', [], {})
        },
        'wiki.helpfulvote': {
            'Meta': {'object_name': 'HelpfulVote'},
            'anonymous_id': ('django.db.models.fields.CharField', [], {'max_length': '40', 'db_index': 'True'}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'django.utils.timezone.now', 'db_index': 'True'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'poll_votes'", 'null': 'True', 'to': "orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'poll_votes'", 'to': "orm['wiki.Document']"}),
            'helpful': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user_agent': ('django.db.models.fields.CharField', [], {'max_length': '1000'})
        },
        'wiki.operatingsystem': {
            'Meta': {'unique_together': "(('item_id', 'document'),)", 'object_name': 'OperatingSystem'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'operating_system_set'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'item_id': ('django.db.models.fields.IntegerField', [], {})
        },
        'wiki.relateddocument': {
            'Meta': {'ordering': "['-in_common']", 'object_name': 'RelatedDocument'},
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_from'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'in_common': ('django.db.models.fields.IntegerField', [], {}),
            'related': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'related_to'", 'to': "orm['wiki.Document']"})
        },
        'wiki.reviewtag': {
            'Meta': {'object_name': 'ReviewTag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'wiki.reviewtaggedrevision': {
            'Meta': {'object_name': 'ReviewTaggedRevision'},
            'content_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Revision']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.ReviewTag']"})
        },
        'wiki.revision': {
            'Meta': {'object_name': 'Revision'},
            'based_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Revision']", 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'django.utils.timezone.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_revisions'", 'to': "orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_mindtouch_migration': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'mindtouch_old_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True', 'db_index': 'True'}),
            'reviewed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviewed_revisions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'show_toc': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'significance': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {}),
            'tags': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'null': 'True', 'db_index': 'True'})
        },
        'wiki.taggeddocument': {
            'Meta': {'object_name': 'TaggedDocument'},
            'content_object': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.DocumentTag']"})
        }
    }

    complete_apps = ['wiki']
