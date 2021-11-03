from django.contrib import admin

from kuma.notifications.models import Notification, CompatibilityData


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    ...
    # raw_id_fields = ["user"]


@admin.register(CompatibilityData)
class CompatibilityDataAdmin(admin.ModelAdmin):
    pass
