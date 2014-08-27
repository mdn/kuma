from django.contrib import admin

from .models import Calendar, Event

admin.site.register(Calendar, admin.ModelAdmin)
admin.site.register(Event, admin.ModelAdmin)
