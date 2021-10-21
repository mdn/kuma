from django.contrib import admin

from kuma.notifications.models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    raw_id_fields = ["user"]
