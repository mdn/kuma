import datetime

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core import validators
from django.core.cache import cache
from django.db import models, transaction
from django.db.models import Max
from django.dispatch import receiver
from django.utils import timezone
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _

from .constants import USERNAME_REGEX


class UserBan(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="bans",
        verbose_name="Banned user",
        on_delete=models.CASCADE,
    )
    by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="bans_issued",
        verbose_name="Banned by",
        on_delete=models.PROTECT,
    )
    reason = models.TextField()
    date = models.DateField(default=datetime.date.today)
    is_active = models.BooleanField(default=True, help_text="(Is ban active)")

    def __str__(self):
        message = _("%(banned_user)s banned by %(banned_by)s") % {
            "banned_user": self.user,
            "banned_by": self.by,
        }
        if not self.is_active:
            message = _("%s (no longer active)") % message
        return message


class User(AbstractUser):
    """
    Our custom user class.
    """

    timezone = models.CharField(
        verbose_name=_("Timezone"),
        max_length=42,
        blank=True,
        default=settings.TIME_ZONE,
        # Note the deliberate omission of the `choices=` here.
        # That's because there's no good way to list all possible
        # timezones as a 2-D tuple. The *name* of the timezone rarely
        # changes but the human-friendly description of it easily does.
    )
    locale = models.CharField(
        max_length=7,
        default=settings.LANGUAGE_CODE,
        choices=settings.SORTED_LANGUAGES,
        verbose_name=_("Language"),
        blank=True,
        db_index=True,
    )
    homepage = models.URLField(
        verbose_name=_("Homepage"),
        max_length=255,
        blank=True,
        error_messages={
            "invalid": _(
                "This URL has an invalid format. "
                "Valid URLs look like http://example.com/my_page."
            )
        },
    )
    title = models.CharField(
        verbose_name=_("Title"),
        max_length=255,
        blank=True,
    )
    fullname = models.CharField(
        verbose_name=_("Name"),
        max_length=255,
        blank=True,
    )
    organization = models.CharField(
        verbose_name=_("Organization"),
        max_length=255,
        blank=True,
    )
    location = models.CharField(
        verbose_name=_("Location"),
        max_length=255,
        blank=True,
    )
    bio = models.TextField(
        verbose_name=_("About Me"),
        blank=True,
    )
    irc_nickname = models.CharField(
        verbose_name=_("IRC nickname"),
        max_length=255,
        blank=True,
    )

    is_newsletter_subscribed = models.BooleanField(default=False)

    WEBSITE_VALIDATORS = {
        "website": validators.RegexValidator(
            r"^https?://",
            _("Enter a valid website URL."),
            "invalid",
        ),
        "twitter": validators.RegexValidator(
            r"^https?://twitter\.com/",
            _("Enter a valid Twitter URL."),
            "invalid",
        ),
        "github": validators.RegexValidator(
            r"^https?://github\.com/",
            _("Enter a valid GitHub URL."),
            "invalid",
        ),
        "stackoverflow": validators.RegexValidator(
            r"^https?://([a-z]{2}\.)?stackoverflow\.com/users/",
            _("Enter a valid Stack Overflow URL."),
            "invalid",
        ),
        "linkedin": validators.RegexValidator(
            r"^https?://((www|\w\w)\.)?linkedin.com/((in/[^/]+/?)|(pub/[^/]+/((\w|\d)+/?){3}))$",
            _("Enter a valid LinkedIn URL."),
            "invalid",
        ),
        "pmo": validators.RegexValidator(
            r"^https?://people\.mozilla\.org/",
            _("Enter a valid PMO URL."),
            "invalid",
        ),
        "facebook": validators.RegexValidator(
            r"^https?://www\.facebook\.com/",
            _("Enter a valid Facebook URL."),
            "invalid",
        ),
        "discourse": validators.RegexValidator(
            r"^https://discourse\.mozilla\.org/u/",
            _("Enter a valid Discourse URL."),
            "invalid",
        ),
    }

    # a bunch of user URLs
    website_url = models.TextField(
        _("Website"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["website"]],
    )
    pmo_url = models.TextField(
        _("Mozilla People Directory"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["pmo"]],
    )
    github_url = models.TextField(
        _("GitHub"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["github"]],
    )
    is_github_url_public = models.BooleanField(
        _("Public GitHub URL"),
        default=False,
    )
    twitter_url = models.TextField(
        _("Twitter"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["twitter"]],
    )
    linkedin_url = models.TextField(
        _("LinkedIn"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["linkedin"]],
    )
    facebook_url = models.TextField(
        _("Facebook"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["facebook"]],
    )
    stackoverflow_url = models.TextField(
        _("Stack Overflow"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["stackoverflow"]],
    )
    discourse_url = models.TextField(
        _("Discourse"),
        blank=True,
        validators=[WEBSITE_VALIDATORS["discourse"]],
    )
    stripe_customer_id = models.CharField(max_length=255, blank=True)

    subscriber_number = models.PositiveIntegerField(blank=True, null=True)

    class Meta:
        db_table = "auth_user"

    @property
    def has_legacy_username(self):
        return not USERNAME_REGEX.search(self.username)

    @cached_property
    def is_beta_tester(self):
        return settings.BETA_GROUP_NAME in self.groups.values_list("name", flat=True)

    @cached_property
    def active_ban(self):
        """
        Returns the first active ban for the user or None.
        """
        return self.bans.filter(is_active=True).first()

    def wiki_revisions(self, count=5):
        return (
            self.created_revisions.prefetch_related("document")
            .defer("content", "summary")
            .order_by("-id")[:count]
        )

    def allows_editing_by(self, user):
        return user.is_staff or user.is_superuser or user.pk == self.pk

    def set_next_subscriber_number_and_save(self):
        assert not self.subscriber_number, "already set"
        lock_key = "set_next_subscriber_number_and_save"
        # By locking "globally", we get to be certain that our query to get
        # the current highest `subscriber_number`, gets done alone.
        with cache.lock(lock_key):
            highest_number = User.get_highest_subscriber_number()
            User.objects.filter(id=self.id).update(subscriber_number=highest_number + 1)

    @classmethod
    def get_highest_subscriber_number(cls):
        return (
            cls.objects.filter(subscriber_number__isnull=False).aggregate(
                number=Max("subscriber_number")
            )["number"]
            or 0
        )


class UserSubscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    stripe_subscription_id = models.CharField(max_length=255, blank=True)
    canceled = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return (
            f"{self.user.username} ({self.stripe_subscription_id})"
            f"{' CANCELED' if self.canceled else ''}"
        )

    @classmethod
    # The reason we make this (class) method transaction atomic is because this
    # use of `update_or_create` will actually trigger a `post_save` signal
    # on the `User` model which will set the `User.subscriber_number` if needed.
    # So, this way we're pre-emptively making sure these two things are atomically
    # connected.
    @transaction.atomic()
    def set_active(cls, user, stripe_subscription_id):
        cls.objects.update_or_create(
            stripe_subscription_id=stripe_subscription_id,
            user=user,
            defaults={"canceled": None, "updated": timezone.now()},
        )

    @classmethod
    def set_canceled(cls, user, stripe_subscription_id):
        cls.objects.update_or_create(
            stripe_subscription_id=stripe_subscription_id,
            user=user,
            defaults={"canceled": timezone.now(), "updated": timezone.now()},
        )


@receiver(models.signals.post_save, sender=UserSubscription)
def set_user_subscriber_number(sender, instance, **kwargs):
    if not instance.canceled and not instance.user.subscriber_number:
        instance.user.set_next_subscriber_number_and_save()
