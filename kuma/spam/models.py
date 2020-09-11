from django.conf import settings
from django.db import models
from django.utils.translation import gettext_lazy as _
from django_extensions.db.fields import CreationDateTimeField


class SpamAttempt(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created = CreationDateTimeField(_("created"), db_index=True)

    class Meta:
        get_latest_by = "created"
        ordering = ("-created",)
        abstract = True


class AkismetSubmission(models.Model):
    """
    Stores the submissions to Akismet that are sent by trusted writers.

    This shall be used as a log of sorts to make sure we know what the data
    has been reported to Akismet as spam or ham.
    """

    SPAM_TYPE, HAM_TYPE = "spam", "ham"
    TYPES = (
        (SPAM_TYPE, _("Spam")),
        (HAM_TYPE, _("Ham")),
    )
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    sent = CreationDateTimeField(_("sent at"), db_index=True,)
    type = models.CharField(_("type"), max_length=4, choices=TYPES, db_index=True,)

    class Meta:
        get_latest_by = "sent"
        ordering = ("-sent",)
        abstract = True
