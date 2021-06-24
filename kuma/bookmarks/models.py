from django.contrib.postgres.fields import ArrayField
from django.db import models

from kuma.documenturls.models import DocumentURL


class Bookmark(models.Model):
    documenturl = models.ForeignKey(
        DocumentURL, on_delete=models.CASCADE, verbose_name="Document URL"
    )
    # Why not a `models.ForeignKey(settings.AUTH_USER_MODEL` here?
    # Because this modal is configured to be used by Postgres and
    # the `settings.AUTH_USER_MODEL` is configured to be used by MySQL.
    # The obvious loss of this "hack" is that we don't get tight reference
    # integrity.
    # Some day, when we finally manage to migrate all the user related fields
    # over to Postgres, we can convert this to a foreign key.
    user_id = models.PositiveIntegerField(verbose_name="User ID")

    notes = ArrayField(models.TextField(), default=list)
    deleted = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Bookmark"
        unique_together = ["documenturl", "user_id"]

    def __str__(self):
        return self.documenturl.uri
