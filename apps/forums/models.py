from django.db import models
from django.contrib.auth.models import User

import jinja2

from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from sumo.models import ModelBase
from sumo.utils import WikiParser
from forums.tasks import build_notification
import forums


class ThreadLockedError(Exception):
    """Trying to create a post in a locked thread."""
    pass


class Forum(ModelBase):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True)
    last_post = models.ForeignKey('Post', related_name='last_post_in_forum',
                                  null=True)

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('forums.threads', kwargs={'forum_slug': self.slug})


class Thread(ModelBase):
    id = models.AutoField(primary_key=True)
    title = models.CharField(max_length=255)
    forum = models.ForeignKey('Forum')
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    creator = models.ForeignKey(User)
    last_post = models.ForeignKey('Post', related_name='last_post_in',
                                  null=True)
    replies = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-is_sticky', '-last_post__created']

    @property
    def last_page(self):
        """Returns the page number for the last post."""
        return self.replies / forums.POSTS_PER_PAGE + 1

    def __unicode__(self):
        return self.title

    def delete(self, *args, **kwargs):
        """Override delete method to update parent forum info."""

        forum = Forum.uncached.get(pk=self.forum.id)
        if forum.last_post and forum.last_post.thread_id == self.id:
            try:
                forum.last_post = Post.objects.filter(thread__forum=forum) \
                                              .exclude(thread=self) \
                                              .order_by('-created')[0]
            except IndexError:
                forum.last_post = None
            forum.save()

        super(Thread, self).delete(*args, **kwargs)

    def new_post(self, author, content):
        """Create a new post, if the thread is unlocked."""
        if self.is_locked:
            raise ThreadLockedError

        return self.post_set.create(author=author, content=content)

    def get_absolute_url(self):
        return reverse('forums.posts',
                       kwargs={'forum_slug': self.forum.slug,
                               'thread_id': self.id})


class Post(ModelBase):
    id = models.AutoField(primary_key=True)
    thread = models.ForeignKey('Thread')
    content = models.TextField()
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return self.content[:50]

    def save(self, *args, **kwargs):
        """Override save method to update parent thread info."""

        new = self.id is None

        super(Post, self).save(*args, **kwargs)

        if new:
            self.thread.replies = self.thread.post_set.count() - 1
            self.thread.last_post = self
            self.thread.save()

            self.thread.forum.last_post = self
            self.thread.forum.save()

            # Send notifications to thread watchers.
            build_notification.delay(self)

    def delete(self, *args, **kwargs):
        """Override delete method to update parent thread info."""

        thread = Thread.uncached.get(pk=self.thread.id)
        if thread.last_post_id and thread.last_post_id == self.id:
            try:
                thread.last_post = thread.post_set.all() \
                                                  .order_by('-created')[1]
            except IndexError:
                # The thread has only one Post so let the delete cascade.
                pass
        thread.replies = thread.post_set.count() - 2
        thread.save()

        forum = Forum.uncached.get(pk=thread.forum.id)
        if forum.last_post_id and forum.last_post_id == self.id:
            try:
                forum.last_post = Post.objects.filter(thread__forum=forum) \
                                              .order_by('-created')[1]
            except IndexError:
                forum.last_post = None
            forum.save()

        super(Post, self).delete(*args, **kwargs)

    @property
    def page(self):
        """Get the page of the thread on which this post is found."""
        t = self.thread
        earlier = t.post_set.filter(created__lte=self.created).count() - 1
        if earlier < 1:
            return 1
        return earlier / forums.POSTS_PER_PAGE + 1

    def get_absolute_url(self):
        query = {}
        if self.page > 1:
            query = {'page': self.page}

        url_ = reverse('forums.posts',
                       kwargs={'forum_slug': self.thread.forum.slug,
                               'thread_id': self.thread.id})
        return urlparams(url_, hash='post-%s' % self.id, **query)

    @property
    def content_parsed(self):
        parser = WikiParser()
        return jinja2.Markup(parser.parse(self.content, False))
