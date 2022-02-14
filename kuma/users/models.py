import json

from django.contrib.auth import get_user_model
from django.db import models


class UserProfile(models.Model):
    class SubscriptionType(models.TextChoices):
        """Choices for MDN Subscription Types, add new subscription plans to be supported here"""

        MDN_PLUS_5M = "mdn_plus_5m", "MDN Plus 5M"
        MDN_PLUS_5Y = "mdn_plus_5y", "MDN Plus 5Y"
        MDN_PLUS_10M = "mdn_plus_10m", "MDN Plus 10M"
        MDN_PLUS_10Y = "mdn_plus_10y", "MDN Plus 10Y"
        NONE = "", "None"

    user = models.OneToOneField(get_user_model(), on_delete=models.CASCADE)
    locale = models.CharField(max_length=6, null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)
    avatar = models.URLField(max_length=512, blank=True, default="")
    fxa_refresh_token = models.CharField(blank=True, default="", max_length=128)
    is_subscriber = models.BooleanField(default=False)
    subscription_type = models.CharField(
        max_length=512,
        blank=True,
        choices=SubscriptionType.choices,
        default=SubscriptionType.NONE,
    )

    class Meta:
        verbose_name = "User profile"

    def __str__(self):
        return json.dumps(
            {
                "uid": self.user.username,
                "is_subscriber": self.is_subscriber,
                "subscription_type": self.subscription_type,
                "email": self.user.email,
                "avatar": self.avatar,
            }
        )


class AccountEvent(models.Model):
    """Stores the Events received from Firefox Accounts.

    Each event is processed by Celery and stored in this table.
    """

    class EventType(models.IntegerChoices):
        """Type of event received from Firefox Accounts."""

        PASSWORD_CHANGED = 1
        PROFILE_CHANGED = 2
        SUBSCRIPTION_CHANGED = 3
        PROFILE_DELETED = 4

    class EventStatus(models.IntegerChoices):
        """Status of each event received from Firefox Accounts."""

        PROCESSED = 1
        PENDING = 2
        IGNORED = 3
        NOT_IMPLEMENTED = 4

    created_at = models.DateTimeField(auto_now_add=True)
    modified_at = models.DateTimeField(auto_now=True)
    # This could be a ForeignKey to the UserProfile table (username). Decoupled for now
    fxa_uid = models.CharField(max_length=128, blank=True, default="")
    payload = models.TextField(max_length=2048, blank=True, default="")
    event_type = models.IntegerField(choices=EventType.choices, default="", blank=True)
    status = models.IntegerField(
        choices=EventStatus.choices, default=EventStatus.PENDING
    )
    jwt_id = models.CharField(max_length=256, blank=True, default="")
    issued_at = models.CharField(max_length=32, default="", blank=True)

    class Meta:
        ordering = ["-modified_at"]
