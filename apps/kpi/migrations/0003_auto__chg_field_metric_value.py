# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Changing field 'Metric.value'
        db.alter_column('kpi_metric', 'value', self.gf('django.db.models.fields.PositiveIntegerField')(null=True))


    def backwards(self, orm):
        
        # User chose to not deal with backwards NULL issues for 'Metric.value'
        raise RuntimeError("Cannot reverse this migration. 'Metric.value' and its values cannot be restored.")


    models = {
        'kpi.metric': {
            'Meta': {'unique_together': "[('kind', 'start', 'end')]", 'object_name': 'Metric'},
            'end': ('django.db.models.fields.DateField', [], {}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'kind': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['kpi.MetricKind']"}),
            'start': ('django.db.models.fields.DateField', [], {}),
            'value': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'})
        },
        'kpi.metrickind': {
            'Meta': {'object_name': 'MetricKind'},
            'code': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '255'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        }
    }

    complete_apps = ['kpi']
