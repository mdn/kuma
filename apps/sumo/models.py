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


class Forum(ModelBase):
    forumId = models.AutoField(primary_key=True)
    name = models.CharField(max_length=255, null=True)
    description = models.TextField(null=True)
    created = models.IntegerField(null=True)
    lastPost = models.IntegerField(null=True)
    threads = models.IntegerField(null=True)
    comments = models.IntegerField(null=True)
    controlFlood = models.CharField(max_length=1, null=True)
    floodInterval = models.IntegerField(null=True)
    moderator = models.CharField(max_length=200, null=True)
    hits = models.IntegerField(null=True)
    mail = models.CharField(max_length=200, null=True)
    useMail = models.CharField(max_length=1, null=True)
    section = models.CharField(max_length=200, null=True)
    usePruneUnreplied = models.CharField(max_length=1, null=True)
    pruneUnrepliedAge = models.IntegerField(null=True)
    usePruneOld = models.CharField(max_length=1, null=True)
    pruneMaxAge = models.IntegerField(null=True)
    topicsPerPage = models.IntegerField(null=True)
    topicOrdering = models.CharField(max_length=100, null=True)
    threadOrdering = models.CharField(max_length=100, null=True)
    att = models.CharField(max_length=80, null=True)
    att_store = models.CharField(max_length=4, null=True)
    att_store_dir = models.CharField(max_length=250, null=True)
    att_max_size = models.IntegerField(null=True)
    ui_level = models.CharField(max_length=1, null=True)
    forum_password = models.CharField(max_length=32, null=True)
    forum_use_password = models.CharField(max_length=1, null=True)
    moderator_group = models.CharField(max_length=200, null=True)
    approval_type = models.CharField(max_length=20, null=True)
    outbound_address = models.CharField(max_length=250, null=True)
    outbound_mails_for_inbound_mails = models.CharField(max_length=1, null=True)
    outbound_mails_reply_link = models.CharField(max_length=1, null=True)
    outbound_from = models.CharField(max_length=250, null=True)
    inbound_pop_server = models.CharField(max_length=250, null=True)
    inbound_pop_port = models.IntegerField(null=True)
    inbound_pop_user = models.CharField(max_length=200, null=True)
    inbound_pop_password = models.CharField(max_length=80, null=True)
    topic_smileys = models.CharField(max_length=1, null=True)
    ui_avatar = models.CharField(max_length=1, null=True)
    ui_flag = models.CharField(max_length=1, null=True)
    ui_posts = models.CharField(max_length=1, null=True)
    ui_email = models.CharField(max_length=1, null=True)
    ui_online = models.CharField(max_length=1, null=True)
    topic_summary = models.CharField(max_length=1, null=True)
    show_description = models.CharField(max_length=1, null=True)
    topics_list_replies = models.CharField(max_length=1, null=True)
    topics_list_reads = models.CharField(max_length=1, null=True)
    topics_list_pts = models.CharField(max_length=1, null=True)
    topics_list_lastpost = models.CharField(max_length=1, null=True)
    topics_list_author = models.CharField(max_length=1, null=True)
    vote_threads = models.CharField(max_length=1, null=True)
    forum_last_n = models.IntegerField(null=True)
    threadStyle = models.CharField(max_length=100, null=True)
    commentsPerPage = models.CharField(max_length=100, null=True)
    is_flat = models.CharField(max_length=1, null=True)

    class Meta:
        db_table = "tiki_forums"

    def __unicode__(self):
        return self.name

    def get_url(self):
        """
        TODO: Once we can use reverse(), use reverse()
        """
        return u'/en/forum/%s' % (self.forumId,)


class ForumThread(ModelBase):
    threadId = models.AutoField(primary_key=True)
    object = models.CharField(max_length=255)
    objectType = models.CharField(max_length=32)
    parentId = models.IntegerField(null=True)
    userName = models.CharField(max_length=200)
    commentDate = models.IntegerField(null=True)
    hits = models.IntegerField(null=True)
    type = models.CharField(max_length=1, null=True)
    points = models.DecimalField(max_digits=8, decimal_places=2, null=True)
    votes = models.IntegerField(null=True)
    average = models.DecimalField(max_digits=8, decimal_places=4, null=True)
    title = models.CharField(max_length=255, null=True)
    data = models.TextField(null=True)
    description = models.CharField(max_length=200, null=True)
    hash = models.CharField(max_length=32, null=True)
    user_ip = models.CharField(max_length=15, null=True)
    summary = models.CharField(max_length=240, null=True)
    smiley = models.CharField(max_length=80, null=True)
    message_id = models.CharField(max_length=128, null=True)
    in_reply_to = models.CharField(max_length=128, null=True)
    comment_rating = models.IntegerField(null=True)

    class Meta:
        db_table = "tiki_comments"

    def __unicode__(self):
        return self.title

    @property
    def name(self):
        return self.title

    @property
    def search_summary(self):
        return self.summary

    def get_url(self):
        """
        TODO: Once we can use reverse(), use reverse()
        """
        return u'/en/forum/%s/%s' % (self.object, self.threadId,)


class WikiPage(ModelBase):
    page_id = models.AutoField(primary_key=True)
    pageName = models.CharField(max_length=160, unique=True)
    hits = models.IntegerField(null=True)
    data = models.TextField(null=True)
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
        return self.pageName

    @property
    def name(self):
        return self.pageName

    def get_url(self):
        """
        TODO: Once we can use reverse(), use reverse()
        """
        name = self.pageName.replace(' ', '+')
        return u'/%s/kb/%s' % (self.lang, name,)


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

