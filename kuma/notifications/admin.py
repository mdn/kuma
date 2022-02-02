from django.contrib import admin

from kuma.notifications.models import Notification, NotificationData, Watch


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    ...


@admin.register(NotificationData)
class NotificationDataAdmin(admin.ModelAdmin):
    ...


@admin.register(Watch)
class WatchAdmin(admin.ModelAdmin):
    ...
