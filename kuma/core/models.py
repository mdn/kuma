from django.db import models
from django.dispatch import receiver
from django.utils import timezone

from .managers import IPBanManager
from .jobs import IPBanJob


class ModelBase(models.Model):
    """Common base model for all MDN models: Implements caching."""

    class Meta:
        abstract = True

    def update(self, **kw):
        """
        Shortcut for doing an UPDATE on this object.

        If _signal=False is in ``kw`` the post_save signal won't be sent.
        """
        signal = kw.pop('_signal', True)
        cls = self.__class__
        for k, v in kw.items():
            setattr(self, k, v)
        if signal:
            # Detect any attribute changes during pre_save and add those to the
            # update kwargs.
            attrs = dict(self.__dict__)
            models.signals.pre_save.send(sender=cls, instance=self)
            for k, v in self.__dict__.items():
                if attrs[k] != v:
                    kw[k] = v
                    setattr(self, k, v)
        cls.objects.filter(pk=self.pk).update(**kw)
        if signal:
            models.signals.post_save.send(sender=cls, instance=self,
                                          created=False)


class IPBan(models.Model):
    ip = models.GenericIPAddressField()
    created = models.DateTimeField(default=timezone.now, db_index=True)
    deleted = models.DateTimeField(null=True, blank=True)

    objects = IPBanManager()

    def delete(self, *args, **kwargs):
        self.deleted = timezone.now()
        self.save()

    def __unicode__(self):
        return u'%s banned on %s' % (self.ip, self.created)


@receiver(models.signals.post_save, sender=IPBan)
@receiver(models.signals.pre_delete, sender=IPBan)
def invalidate_ipban_caches(sender, instance, **kwargs):
    IPBanJob().invalidate(instance.ip)
