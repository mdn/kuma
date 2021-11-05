from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    users = models.ManyToManyField(User)
    title = models.CharField(max_length=256)
    text = models.CharField(max_length=256)
    read = models.BooleanField(default=False)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def serialize(self):
        return {
            "id": self.id,
            "title": self.title,
            "text": self.text,
            "created": self.created,
            "read": self.read,
        }

    def __str__(self):
        return self.title


class CompatibilityData(models.Model):
    bcd = models.JSONField()
    created = models.DateTimeField(auto_now_add=True)
