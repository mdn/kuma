from django.contrib.auth.models import User
from django.db import models

from kuma.documenturls.models import DocumentURL


class Bookmark(models.Model):
    documenturl = models.ForeignKey(
        DocumentURL, on_delete=models.CASCADE, verbose_name="Document URL"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    notes = models.JSONField(default=list)
    deleted = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bookmark"
        unique_together = ["documenturl", "user_id"]

    def __str__(self):
        return self.documenturl.uri
