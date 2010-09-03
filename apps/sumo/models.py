from django.conf import settings
from django.db import models

import caching.base
from taggit.managers import TaggableManager

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


class TaggableMixin(models.Model):
    """Mixin for taggable models that still allows caching manager to be the
    default manager

    Mix this in after ModelBase.

    """
    tags = TaggableManager()

    class Meta:
        abstract = True


class WikiPage(ModelBase):
    page_id = models.AutoField(primary_key=True)
    title = models.CharField(db_column='pageName', max_length=160, unique=True)
    hits = models.IntegerField(null=True)
    content = models.TextField(db_column='data', null=True)
    description = models.CharField(max_length=200, null=True)
    desc_auto = models.CharField(max_length=1)
    lastModif = models.IntegerField(null=True)
    comment = models.CharField(max_length=200, null=True)
    version = models.IntegerField(null=True, default=0)
    user = models.CharField(max_length=200, null=True)
    ip = models.CharField(max_length=15, null=True)
    flag = models.CharField(max_length=1, null=True)
    points = models.IntegerField(null=True)
    votes = models.IntegerField(null=True)
    cache = models.TextField(null=True)
    wiki_cache = models.IntegerField(null=True)
    cache_timestamp = models.IntegerField(null=True)
    pageRank = models.DecimalField(max_digits=4, decimal_places=3, null=True)
    creator = models.CharField(max_length=200, null=True)
    page_size = models.PositiveIntegerField(null=True)
    lang = models.CharField(max_length=16, null=True)
    lockedby = models.CharField(max_length=200, null=True)
    is_html = models.NullBooleanField(null=True)
    created = models.IntegerField(null=True)
    keywords = models.TextField(null=True)

    class Meta:
        db_table = "tiki_pages"

    def __unicode__(self):
        return self.title

    @property
    def name(self):
        return self.title

    def get_url(self):
        """
        TODO: Once we can use reverse(), use reverse(), and turn this into
        get_absolute_url, below.
        """
        name = self.title.replace(' ', '+')

        if self.lang in INTERNAL_MAP:
            lang = INTERNAL_MAP[self.lang]
        else:
            lang = self.lang

        return u'/%s/kb/%s' % (lang, name,)

    get_absolute_url = get_url

    def get_edit_url(self):
        """
        TODO: Once we can use reverse(), use reverse()
        """
        return settings.WIKI_EDIT_URL % self.title.replace(' ', '+')

    @classmethod
    def get_create_url(cls, name):
        """
        TODO: Once we can use reverse(), use reverse()
        """
        return settings.WIKI_CREATE_URL % name.replace(' ', '+')


class Category(ModelBase):
    categId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, null=True)
    description = models.CharField(max_length=250, null=True)
    parentId = models.IntegerField(null=True)
    hits = models.IntegerField(null=True)

    class Meta:
        db_table = "tiki_categories"

    def __unicode__(self):
        return self.name


class Session(ModelBase):
    class Meta:
        db_table = 'tiki_sessions'

    sessionId = models.CharField(unique=True,
        primary_key=True, max_length=32)
    user = models.CharField(max_length=200)
    timestamp = models.IntegerField(null=True)
    tikihost = models.CharField(max_length=200, null=True)

    def __unicode__(self):
        return '%s: %s' % (self.sessionId, self.user)


class TikiUser(ModelBase):
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
