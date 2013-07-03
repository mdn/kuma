# encoding: utf-8
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import datetime
from south.db import db
from south.v2 import DataMigration
from django.db import models

from kpi.models import L10N_METRIC_CODE

class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        l10n_metric = orm.MetricKind(code=L10N_METRIC_CODE)
        l10n_metric.save()


    def backwards(self, orm):
        "Write your backwards methods here."
        l10n_metric = orm.MetricKind.get(code=L10N_METRIC_CODE)
        l10n_metric.delete()



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
