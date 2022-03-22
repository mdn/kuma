from django.conf import settings
from django.contrib.auth.models import User
from django.db import models


class NotificationData(models.Model):
    title = models.CharField(max_length=256)
    text = models.CharField(max_length=256)
    type = models.CharField(
        max_length=32,
        choices=(("content", "content"), ("compat", "compat")),
        default="compat",
    )
    # Storing the page url in the notification because the watch object might be deleted if the user
    # unsubscribes
    page_url = models.TextField()
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    notification = models.ForeignKey(NotificationData, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    starred = models.BooleanField(default=False)
    read = models.BooleanField(default=False)
    deleted = models.BooleanField(default=False)

    def serialize(self):
        return {
            "id": self.id,
            "title": self.notification.title,
            "text": self.notification.text,
            "created": self.notification.created,
            "read": self.read,
            "starred": self.starred,
            "url": self.notification.page_url,
        }

    def __str__(self):
        return self.notification.title


class Watch(models.Model):
    users = models.ManyToManyField(User, through="UserWatch")
    title = models.CharField(max_length=2048)
    url = models.TextField()
    path = models.CharField(max_length=4096)

    def __str__(self):
        return f"<Watchers for: {self.url}, {self.path}>"


class CustomBaseModel(models.Model):
    content_updates = models.BooleanField(default=True)
    browser_compatibility = models.JSONField(default=list)

    class Meta:
        abstract = True

    def custom_serialize(self):
        return {
            "content": self.content_updates,
            "compatibility": self.browser_compatibility,
        }


class UserWatch(CustomBaseModel):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    watch = models.ForeignKey(Watch, on_delete=models.CASCADE)
    custom = models.BooleanField(default=False)
    custom_default = models.BooleanField(default=False)

    class Meta:
        db_table = "notifications_watch_users"

    def serialize(self):
        return {
            "title": self.watch.title,
            "url": self.watch.url,
            "path": self.watch.path,
            "custom": self.watch.custom,
            "custom_default": self.watch.custom_default,
        }

    def __str__(self):
        return f"User {self.user_id} watching {self.watch_id}"


class DefaultWatch(CustomBaseModel):
    user = models.OneToOneField(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
