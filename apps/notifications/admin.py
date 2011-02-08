from django.contrib import admin

from notifications.models import EventWatch


class EventWatchAdmin(admin.ModelAdmin):
    list_filter = ('content_type', 'event_type', 'locale')


admin.site.register(EventWatch, EventWatchAdmin)
