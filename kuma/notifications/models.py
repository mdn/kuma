from django.contrib.auth.models import User
from django.db import models


class NotificationData(models.Model):
    title = models.CharField(max_length=256)
    text = models.CharField(max_length=256)
    data = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    notification = models.ForeignKey(NotificationData, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    read = models.BooleanField(default=False)

    def serialize(self):
        return {
            "id": self.id,
            "title": self.notification.title,
            "text": self.notification.text,
            "created": self.notification.created,
            "read": self.read,
        }

    def __str__(self):
        return self.notification.title


class Watch(models.Model):
    users = models.ManyToManyField(User)
    title = models.CharField(max_length=2048)
    url = models.TextField()
    path = models.CharField(max_length=4096)

    def serialize(self):
        return {
            "title": self.title,
            "url": self.url,
            "path": self.path,
        }

    def __str__(self):
        return f"<Watchers for: {self.url}, {self.path}>"
