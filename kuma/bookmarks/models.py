from django.contrib.auth.models import User
from django.db import models

from kuma.documenturls.models import DocumentURL


class Bookmark(models.Model):
    documenturl = models.ForeignKey(
        DocumentURL, on_delete=models.CASCADE, verbose_name="Document URL"
    )
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    custom_name = models.CharField(max_length=500, blank=True)
    notes = models.CharField(max_length=500, blank=True)
    deleted = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bookmark"
        unique_together = ["documenturl", "user_id"]

    def save(self, *args, **kwargs):
        if self.custom_name == self.documenturl.metadata["title"]:
            self.custom_name = ""
        super().save(*args, **kwargs)

    def __str__(self):
        return self.documenturl.uri

    @property
    def title(self):
        return self.custom_name or self.documenturl.metadata["title"]
