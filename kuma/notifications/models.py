from django.contrib.auth.models import User
from django.db import models


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    title = models.CharField(max_length=256)
    text = models.CharField(max_length=256)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    def serialize(self):
        return {
            "id": self.id,
        }

    def __str__(self):
        return self.title
