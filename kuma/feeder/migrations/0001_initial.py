# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Bundle'
        db.create_table('feeder_bundle', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shortname', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
        ))
        db.send_create_signal('feeder', ['Bundle'])

        # Adding M2M table for field feeds on 'Bundle'
        m2m_table_name = db.shorten_name('feeder_bundle_feeds')
        db.create_table(m2m_table_name, (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bundle', models.ForeignKey(orm['feeder.bundle'], null=False)),
            ('feed', models.ForeignKey(orm['feeder.feed'], null=False))
        ))
        db.create_unique(m2m_table_name, ['bundle_id', 'feed_id'])

        # Adding model 'Feed'
        db.create_table('feeder_feed', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shortname', self.gf('django.db.models.fields.SlugField')(unique=True, max_length=50)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=140)),
            ('url', self.gf('django.db.models.fields.CharField')(max_length=2048)),
            ('etag', self.gf('django.db.models.fields.CharField')(max_length=140)),
            ('last_modified', self.gf('django.db.models.fields.DateTimeField')()),
            ('enabled', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('disabled_reason', self.gf('django.db.models.fields.CharField')(max_length=2048, blank=True)),
            ('keep', self.gf('django.db.models.fields.PositiveIntegerField')(default=0)),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('feeder', ['Feed'])

        # Adding model 'Entry'
        db.create_table('feeder_entry', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('feed', self.gf('django.db.models.fields.related.ForeignKey')(related_name='entries', to=orm['feeder.Feed'])),
            ('guid', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('raw', self.gf('django.db.models.fields.TextField')()),
            ('visible', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('last_published', self.gf('django.db.models.fields.DateTimeField')()),
            ('created', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('updated', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, blank=True)),
        ))
        db.send_create_signal('feeder', ['Entry'])

        # Adding unique constraint on 'Entry', fields ['feed', 'guid']
        db.create_unique('feeder_entry', ['feed_id', 'guid'])


    def backwards(self, orm):
        # Removing unique constraint on 'Entry', fields ['feed', 'guid']
        db.delete_unique('feeder_entry', ['feed_id', 'guid'])

        # Deleting model 'Bundle'
        db.delete_table('feeder_bundle')

        # Removing M2M table for field feeds on 'Bundle'
        db.delete_table(db.shorten_name('feeder_bundle_feeds'))

        # Deleting model 'Feed'
        db.delete_table('feeder_feed')

        # Deleting model 'Entry'
        db.delete_table('feeder_entry')


    models = {
        'feeder.bundle': {
            'Meta': {'object_name': 'Bundle'},
            'feeds': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'bundles'", 'blank': 'True', 'to': "orm['feeder.Feed']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shortname': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'})
        },
        'feeder.entry': {
            'Meta': {'ordering': "['-last_published']", 'unique_together': "(('feed', 'guid'),)", 'object_name': 'Entry'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'feed': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'entries'", 'to': "orm['feeder.Feed']"}),
            'guid': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'last_published': ('django.db.models.fields.DateTimeField', [], {}),
            'raw': ('django.db.models.fields.TextField', [], {}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'visible': ('django.db.models.fields.BooleanField', [], {'default': 'True'})
        },
        'feeder.feed': {
            'Meta': {'object_name': 'Feed'},
            'created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'disabled_reason': ('django.db.models.fields.CharField', [], {'max_length': '2048', 'blank': 'True'}),
            'enabled': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'etag': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'keep': ('django.db.models.fields.PositiveIntegerField', [], {'default': '0'}),
            'last_modified': ('django.db.models.fields.DateTimeField', [], {}),
            'shortname': ('django.db.models.fields.SlugField', [], {'unique': 'True', 'max_length': '50'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '140'}),
            'updated': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'blank': 'True'}),
            'url': ('django.db.models.fields.CharField', [], {'max_length': '2048'})
        }
    }

    complete_apps = ['feeder']