from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from django_extensions.db.fields import CreationDateTimeField


class SpamAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL)
    created = CreationDateTimeField(_('created'), db_index=True)

    class Meta:
        get_latest_by = 'created'
        ordering = ('-created',)
        abstract = True
