# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'MetricKind'
        db.create_table('kpi_metrickind', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('code', self.gf('django.db.models.fields.CharField')(unique=True, max_length=255)),
        ))
        db.send_create_signal('kpi', ['MetricKind'])

        # Adding model 'Metric'
        db.create_table('kpi_metric', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('kind', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['kpi.MetricKind'])),
            ('start', self.gf('django.db.models.fields.DateField')()),
            ('end', self.gf('django.db.models.fields.DateField')()),
            ('value', self.gf('django.db.models.fields.PositiveIntegerField')()),
        ))
        db.send_create_signal('kpi', ['Metric'])

        # Adding unique constraint on 'Metric', fields ['kind', 'start', 'end']
        db.create_unique('kpi_metric', ['kind_id', 'start', 'end'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'Metric', fields ['kind', 'start', 'end']
        db.delete_unique('kpi_metric', ['kind_id', 'start', 'end'])

        # Deleting model 'MetricKind'
        db.delete_table('kpi_metrickind')

        # Deleting model 'Metric'
        db.delete_table('kpi_metric')


    models = {
        'kpi.metric': {
            'Meta': {'unique_together': "[('kind', 'start', 'end')]", 'object_name': 'Metric'},
            'end': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['kpi.MetricKind']"}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'value': ('django.db.models.fields.PositiveIntegerField', [], {})
        },
        'kpi.metrickind': {
            'Meta': {'object_name': 'MetricKind'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['kpi']
