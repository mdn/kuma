from django.contrib import admin

from kpi.models import Metric, MetricKind


class MetricAdmin(admin.ModelAdmin):
    list_display = ['kind', 'start', 'end', 'value']
    list_filter = ['kind']


class MetricKindAdmin(admin.ModelAdmin):
    pass


admin.site.register(Metric, MetricAdmin)
admin.site.register(MetricKind, MetricKindAdmin)
