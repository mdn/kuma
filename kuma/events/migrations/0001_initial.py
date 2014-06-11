# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models


class Migration(SchemaMigration):

    def forwards(self, orm):
        # Adding model 'Calendar'
        db.create_table('devmo_calendar', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('shortname', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('url', self.gf('django.db.models.fields.URLField')(unique=True, max_length=200)),
        ))
        db.send_create_signal('events', ['Calendar'])

        # Adding model 'Event'
        db.create_table('devmo_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
            ('end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('conference', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('conference_link', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('location', self.gf('django.db.models.fields.CharField')(max_length=255)),
            ('people', self.gf('django.db.models.fields.TextField')()),
            ('description', self.gf('django.db.models.fields.TextField')()),
            ('done', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('materials', self.gf('django.db.models.fields.URLField')(max_length=200, blank=True)),
            ('calendar', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['events.Calendar'])),
        ))
        db.send_create_signal('events', ['Event'])


    def backwards(self, orm):
        # Deleting model 'Calendar'
        db.delete_table('devmo_calendar')

        # Deleting model 'Event'
        db.delete_table('devmo_event')


    models = {
        'events.calendar': {
            'Meta': {'object_name': 'Calendar', 'db_table': "'devmo_calendar'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shortname': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'url': ('django.db.models.fields.URLField', [], {'unique': 'True', 'max_length': '200'})
        },
        'events.event': {
            'Meta': {'ordering': "['date']", 'object_name': 'Event', 'db_table': "'devmo_event'"},
            'calendar': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['events.Calendar']"}),
            'conference': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'conference_link': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {}),
            'done': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'location': ('django.db.models.fields.CharField', [], {'max_length': '255'}),
            'materials': ('django.db.models.fields.URLField', [], {'max_length': '200', 'blank': 'True'}),
            'people': ('django.db.models.fields.TextField', [], {})
        }
    }

    complete_apps = ['events']