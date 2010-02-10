from django.db import models

import caching.base

# Our apps should subclass BaseManager instead of models.Manager or
# caching.base.CachingManager directly.
ManagerBase = caching.base.CachingManager

class ModelBase(caching.base.CachingMixin, models.Model):
    """
    Base class for SUMO models to abstract some common features.

    * Caching.
    """

    objects = ManagerBase()

    class Meta:
        abstract = True


class ForumThread(ModelBase):
    threadId = models.AutoField(primary_key=True)
    object = models.CharField(max_length=255)
    objectType = models.CharField(max_length=32)
    parentId = models.IntegerField()
    userName = models.CharField(max_length=200)
    commentDate = models.IntegerField()
    hits = models.IntegerField()
    type = models.CharField(max_length=1)
    points = models.DecimalField(max_digits=8,decimal_places=2)
    votes = models.IntegerField()
    average = models.DecimalField(max_digits=8,decimal_places=4)
    title = models.CharField(max_length=255)
    data = models.TextField()
    description = models.CharField(max_length=200)
    hash = models.CharField(max_length=32)
    user_ip = models.CharField(max_length=15)
    summary = models.CharField(max_length=240)
    smiley = models.CharField(max_length=80)
    message_id = models.CharField(max_length=128)
    in_reply_to = models.CharField(max_length=128)
    comment_rating = models.IntegerField()

    class Meta:
        db_table = "tiki_comments"

    def __unicode__(self):
        return self.title

    @property
    def name(self):
        return self.title

    def get_url(self):
        """
        TODO: Once we can use reverse(), use reverse()
        """
        return u'/en/forum/%s/%s' % (self.object, self.threadId,)


class WikiPage(ModelBase):
    page_id = models.AutoField(primary_key=True)
    pageName = models.CharField(max_length=160,unique=True)
    hits = models.IntegerField()
    data = models.TextField()
    description = models.CharField(max_length=200)
    desc_auto = models.CharField(max_length=1)
    lastModif = models.IntegerField()
    comment = models.CharField(max_length=200)
    version = models.IntegerField()
    user = models.CharField(max_length=200)
    ip = models.CharField(max_length=15)
    flag = models.CharField(max_length=1)
    points = models.IntegerField()
    votes = models.IntegerField()
    cache = models.TextField()
    wiki_cache = models.IntegerField()
    cache_timestamp = models.IntegerField()
    pageRank = models.DecimalField(max_digits=4,decimal_places=3)
    creator = models.CharField(max_length=200)
    page_size = models.PositiveIntegerField()
    lang = models.CharField(max_length=16)
    lockedby = models.CharField(max_length=200)
    is_html = models.BooleanField()
    created = models.IntegerField()
    keywords = models.TextField()

    class Meta:
        db_table = "tiki_pages"

    def __unicode__(self):
        return self.pageName

    @property
    def name(self):
        return self.pageName

    def get_url(self):
        """
        TODO: Once we can use reverse(), use reverse()
        """
        return u'/%s/kb/%s' % (self.lang, self.pageName,)

