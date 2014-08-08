# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Document'
        db.create_table('wiki_document', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('slug', self.gf('django.db.models.fields.CharField')(max_length=255, db_index=True)),
            ('is_template', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('is_localizable', self.gf('django.db.models.fields.BooleanField')(default=True, db_index=True)),
            ('locale', self.gf('sumo.models.LocaleField')(default='en-US', max_length=7, db_index=True)),
            ('current_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='current_for+', null=True, to=orm['wiki.Revision'])),
            ('parent', self.gf('django.db.models.fields.related.ForeignKey')(blank=True, related_name='translations', null=True, to=orm['wiki.Document'])),
            ('html', self.gf('django.db.models.fields.TextField')()),
            ('category', self.gf('django.db.models.fields.IntegerField')(db_index=True)),
        ))
        db.send_create_signal('wiki', ['Document'])

        # Adding unique constraint on 'Document', fields ['parent', 'locale']
        db.create_unique('wiki_document', ['parent_id', 'locale'])

        # Adding unique constraint on 'Document', fields ['title', 'locale']
        db.create_unique('wiki_document', ['title', 'locale'])

        # Adding unique constraint on 'Document', fields ['slug', 'locale']
        db.create_unique('wiki_document', ['slug', 'locale'])

        # Adding model 'Revision'
        db.create_table('wiki_revision', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='revisions', to=orm['wiki.Document'])),
            ('summary', self.gf('django.db.models.fields.TextField')()),
            ('content', self.gf('django.db.models.fields.TextField')()),
            ('keywords', self.gf('django.db.models.fields.CharField')(max_length=255, blank=True)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now)),
            ('reviewed', self.gf('django.db.models.fields.DateTimeField')(null=True)),
            ('significance', self.gf('django.db.models.fields.IntegerField')(null=True)),
            ('comment', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('reviewer', self.gf('django.db.models.fields.related.ForeignKey')(related_name='reviewed_revisions', null=True, to=orm['auth.User'])),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='created_revisions', to=orm['auth.User'])),
            ('is_approved', self.gf('django.db.models.fields.BooleanField')(default=False, db_index=True)),
            ('based_on', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['wiki.Revision'], null=True, blank=True)),
        ))
        db.send_create_signal('wiki', ['Revision'])

        # Adding model 'FirefoxVersion'
        db.create_table('wiki_firefoxversion', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item_id', self.gf('django.db.models.fields.IntegerField')()),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='firefox_version_set', to=orm['wiki.Document'])),
        ))
        db.send_create_signal('wiki', ['FirefoxVersion'])

        # Adding unique constraint on 'FirefoxVersion', fields ['item_id', 'document']
        db.create_unique('wiki_firefoxversion', ['item_id', 'document_id'])

        # Adding model 'OperatingSystem'
        db.create_table('wiki_operatingsystem', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('item_id', self.gf('django.db.models.fields.IntegerField')()),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='operating_system_set', to=orm['wiki.Document'])),
        ))
        db.send_create_signal('wiki', ['OperatingSystem'])

        # Adding unique constraint on 'OperatingSystem', fields ['item_id', 'document']
        db.create_unique('wiki_operatingsystem', ['item_id', 'document_id'])

        # Adding model 'HelpfulVote'
        db.create_table('wiki_helpfulvote', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='poll_votes', to=orm['wiki.Document'])),
            ('helpful', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(default=datetime.datetime.now, db_index=True)),
            ('creator', self.gf('django.db.models.fields.related.ForeignKey')(related_name='poll_votes', null=True, to=orm['auth.User'])),
            ('anonymous_id', self.gf('django.db.models.fields.CharField')(max_length=40, db_index=True)),
            ('user_agent', self.gf('django.db.models.fields.CharField')(max_length=1000)),
        ))
        db.send_create_signal('wiki', ['HelpfulVote'])

        # Adding model 'RelatedDocument'
        db.create_table('wiki_relateddocument', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('document', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_from', to=orm['wiki.Document'])),
            ('related', self.gf('django.db.models.fields.related.ForeignKey')(related_name='related_to', to=orm['wiki.Document'])),
            ('in_common', self.gf('django.db.models.fields.IntegerField')()),
        ))
        db.send_create_signal('wiki', ['RelatedDocument'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'OperatingSystem', fields ['item_id', 'document']
        db.delete_unique('wiki_operatingsystem', ['item_id', 'document_id'])

        # Removing unique constraint on 'FirefoxVersion', fields ['item_id', 'document']
        db.delete_unique('wiki_firefoxversion', ['item_id', 'document_id'])

        # Removing unique constraint on 'Document', fields ['slug', 'locale']
        db.delete_unique('wiki_document', ['slug', 'locale'])

        # Removing unique constraint on 'Document', fields ['title', 'locale']
        db.delete_unique('wiki_document', ['title', 'locale'])

        # Removing unique constraint on 'Document', fields ['parent', 'locale']
        db.delete_unique('wiki_document', ['parent_id', 'locale'])

        # Deleting model 'Document'
        db.delete_table('wiki_document')

        # Deleting model 'Revision'
        db.delete_table('wiki_revision')

        # Deleting model 'FirefoxVersion'
        db.delete_table('wiki_firefoxversion')

        # Deleting model 'OperatingSystem'
        db.delete_table('wiki_operatingsystem')

        # Deleting model 'HelpfulVote'
        db.delete_table('wiki_helpfulvote')

        # Deleting model 'RelatedDocument'
        db.delete_table('wiki_relateddocument')


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
        'notifications.watch': {
            'Meta': {'object_name': 'Watch'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']", 'null': 'True', 'blank': 'True'}),
            'email': ('django.db.models.fields.EmailField', [], {'db_index': 'True', 'max_length': '75', 'null': 'True', 'blank': 'True'}),
            'event_type': ('django.db.models.fields.CharField', [], {'max_length': '30', 'db_index': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'object_id': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'db_index': 'True'}),
            'secret': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'null': 'True', 'blank': 'True'})
        },
        'taggit.tag': {
            'Meta': {'object_name': 'Tag'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'slug': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '100', 'db_index': 'True'})
        },
        'taggit.taggeditem': {
            'Meta': {'object_name': 'TaggedItem'},
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_tagged_items'", 'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'object_id': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'tag': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'taggit_taggeditem_items'", 'to': "orm['taggit.Tag']"})
        },
        'wiki.document': {
            'Meta': {'unique_together': "(('parent', 'locale'), ('title', 'locale'), ('slug', 'locale'))", 'object_name': 'Document'},
            'category': ('django.db.models.fields.IntegerField', [], {'db_index': 'True'}),
            'current_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'current_for+'", 'null': 'True', 'to': "orm['wiki.Revision']"}),
            'html': ('django.db.models.fields.TextField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_localizable': ('django.db.models.fields.BooleanField', [], {'default': 'True', 'db_index': 'True'}),
            'is_template': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'locale': ('sumo.models.LocaleField', [], {'default': "'en-US'", 'max_length': '7', 'db_index': 'True'}),
            'parent': ('django.db.models.fields.related.ForeignKey', [], {'blank': 'True', 'related_name': "'translations'", 'null': 'True', 'to': "orm['wiki.Document']"}),
            'related_documents': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['wiki.Document']", 'through': "orm['wiki.RelatedDocument']", 'symmetrical': 'False'}),
            'slug': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '255', 'db_index': 'True'})
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
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now', 'db_index': 'True'}),
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
        'wiki.revision': {
            'Meta': {'object_name': 'Revision'},
            'based_on': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['wiki.Revision']", 'null': 'True', 'blank': 'True'}),
            'comment': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'content': ('django.db.models.fields.TextField', [], {}),
            'created': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'creator': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'created_revisions'", 'to': "orm['auth.User']"}),
            'document': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'revisions'", 'to': "orm['wiki.Document']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_approved': ('django.db.models.fields.BooleanField', [], {'default': 'False', 'db_index': 'True'}),
            'keywords': ('django.db.models.fields.CharField', [], {'max_length': '255', 'blank': 'True'}),
            'reviewed': ('django.db.models.fields.DateTimeField', [], {'null': 'True'}),
            'reviewer': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'reviewed_revisions'", 'null': 'True', 'to': "orm['auth.User']"}),
            'significance': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'summary': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['wiki']
