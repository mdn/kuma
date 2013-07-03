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
        
        # Adding model 'Constance'
        db.create_table('constance_config', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('key', self.gf('django.db.models.fields.TextField')()),
            ('value', self.gf('picklefield.fields.PickledObjectField')()),
        ))
        db.send_create_signal('database', ['Constance'])


    def backwards(self, orm):
        
        # Deleting model 'Constance'
        db.delete_table('constance_config')


    models = {
        'database.constance': {
            'Meta': {'object_name': 'Constance', 'db_table': "'constance_config'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'key': ('django.db.models.fields.TextField', [], {}),
            'value': ('picklefield.fields.PickledObjectField', [], {})
        }
    }

    complete_apps = ['database']
