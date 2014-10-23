# -*- coding: utf-8 -*-
from django.db.utils import IntegrityError
from south.v2 import DataMigration
from django.contrib.sites.models import Site


class Migration(DataMigration):

    def forwards(self, orm):
        "Write your forwards methods here."
        try:
            Site.objects.create(pk=1,
                                name='developer.mozilla.org',
                                domain='developer.mozilla.org')
        except IntegrityError:
            # already exists
            pass

    def backwards(self, orm):
        pass

    models = {}
    complete_apps = ['devmo']
    symmetrical = True
