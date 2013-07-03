# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib import admin

from kpi.models import Metric, MetricKind


class MetricAdmin(admin.ModelAdmin):
    list_display = ['kind', 'start', 'end', 'value']
    list_filter = ['kind']


class MetricKindAdmin(admin.ModelAdmin):
    pass


admin.site.register(Metric, MetricAdmin)
admin.site.register(MetricKind, MetricKindAdmin)
