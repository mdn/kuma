import json

from django.contrib.auth import get_user_model
from django.db import models


class UserProfile(models.Model):
    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    locale = models.CharField(max_length=6, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    fxa_uid = models.CharField(max_length=255, null=True, blank=True, unique=True)
    avatar = models.URLField(max_length=512, blank=True, default="")
    fxa_refresh_token = models.CharField(blank=True, default="", max_length=128)

    class Meta:
        verbose_name = "User profile"

    def __str__(self):
        return json.dumps(
            {
                "uid": self.fxa_uid,
                "is_subscriber": self.user.is_active,
                "email": self.user.email,
                "avatar": self.avatar,
            }
        )
