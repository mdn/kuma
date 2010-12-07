from django.conf import settings
from django.db import models

import caching.base

from sumo_locales import INTERNAL_MAP

# Our apps should subclass ManagerBase instead of models.Manager or
# caching.base.CachingManager directly.
ManagerBase = caching.base.CachingManager


class ModelBase(caching.base.CachingMixin, models.Model):
    """
    Base class for SUMO models to abstract some common features.

    * Caching.
    """

    objects = ManagerBase()
    uncached = models.Manager()

    class Meta:
        abstract = True


class TikiUser(ModelBase):
    # TODO: Delete me!
    class Meta:
        db_table = 'users_users'

    userId = models.AutoField(primary_key=True)
    email = models.CharField(max_length=200, null=True)
    login = models.CharField(max_length=200, unique=True)
    password = models.CharField(max_length=30)
    provpass = models.CharField(max_length=30)
    default_group = models.CharField(max_length=30, null=True)
    lastLogin = models.IntegerField(null=True)
    currentLogin = models.IntegerField(null=True)
    registrationDate = models.IntegerField(null=True)
    challenge = models.CharField(max_length=32, null=True)
    pass_confirm = models.IntegerField(null=True)
    email_confirm = models.IntegerField(null=True)
    hash = models.CharField(max_length=34, null=True)
    created = models.IntegerField(null=True)
    avatarName = models.CharField(max_length=80, null=True)
    avatarSize = models.IntegerField(null=True)
    avatarFileType = models.CharField(max_length=250, null=True)
    avatarData = models.TextField(null=True)
    avatarLibName = models.CharField(max_length=200, null=True)
    avatarType = models.CharField(max_length=1, null=True)
    score = models.IntegerField(default=0)
    unsuccessful_logins = models.IntegerField(default=0)
    valid = models.CharField(max_length=32, null=True)
    openid_url = models.CharField(max_length=255, null=True)
    livechat_id = models.CharField(max_length=255, null=True, unique=True)

    def __unicode__(self):
        return '%s: %s' % (self.userId, self.login)
