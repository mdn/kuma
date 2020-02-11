from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from .jobs import BannedIPsJob
from .managers import IPBanManager


class IPBan(models.Model):
    """
    Ban an IP address.

    Currently, this only bans an IP address from editing.
    """

    ip = models.GenericIPAddressField()
    created = models.DateTimeField(default=timezone.now, db_index=True)
    deleted = models.DateTimeField(null=True, blank=True)

    objects = IPBanManager()

    def delete(self, *args, **kwargs):
        self.deleted = timezone.now()
        self.save()

    def __str__(self):
        return f"{self.ip} banned on {self.created}"


@receiver(models.signals.post_save, sender=IPBan)
@receiver(models.signals.pre_delete, sender=IPBan)
def invalidate_ipban_caches(sender, instance, **kwargs):
    BannedIPsJob().invalidate()
