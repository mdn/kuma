import datetime

from django.db import models
from django.contrib.auth.models import User

from access import has_perm, perm_is_defined_on
from notifications.models import NotificationsMixin
from sumo.helpers import urlparams, wiki_to_html
from funfactory.urlresolvers import reverse
from sumo.models import ModelBase
import forums


def _last_post_from(posts, exclude_post=None):
    """Return the most recent post in the given set, excluding the given post.

    If there are none, return None.

    """
    if exclude_post:
        posts = posts.exclude(id=exclude_post.id)
    posts = posts.order_by('-created')
    try:
        return posts[0]
    except IndexError:
        return None


class ThreadLockedError(Exception):
    """Trying to create a post in a locked thread."""


class Forum(NotificationsMixin, ModelBase):
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)
    description = models.TextField(null=True)
    last_post = models.ForeignKey('Post', related_name='last_post_in_forum',
                                  null=True)

    class Meta(object):
        permissions = (
                ('view_in_forum',
                 'Can view restricted forums'),
                ('post_in_forum',
                 'Can post in restricted forums'))

    def __unicode__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('forums.threads', kwargs={'forum_slug': self.slug})

    def allows_viewing_by(self, user):
        """Return whether a user can view me, my threads, and their posts."""
        return (self._allows_public_viewing() or
                has_perm(user, 'forums_forum.view_in_forum', self))

    def _allows_public_viewing(self):
        """Return whether I am a world-readable forum.

        If a django-authority permission relates to me, I am considered non-
        public. (We assume that you attached a permission to me in order to
        assign it to some users or groups.) Considered adding a Public flag to
        this model, but we didn't want it to show up on form and thus be
        accidentally flippable by readers of the Admin forum, who are all
        privileged enough to do so.

        """
        return not perm_is_defined_on('forums_forum.view_in_forum', self)

    def allows_posting_by(self, user):
        """Return whether a user can make threads and posts in me."""
        return (self._allows_public_posting() or
                has_perm(user, 'forums_forum.post_in_forum', self))

    def _allows_public_posting(self):
        """Return whether I am a world-writable forum."""
        return not perm_is_defined_on('forums_forum.post_in_forum', self)

    def update_last_post(self, exclude_thread=None, exclude_post=None):
        """Set my last post to the newest, excluding given thread and post."""
        posts = Post.objects.filter(thread__forum=self)
        if exclude_thread:
            posts = posts.exclude(thread=exclude_thread)
        self.last_post = _last_post_from(posts, exclude_post=exclude_post)


class Thread(NotificationsMixin, ModelBase):
    title = models.CharField(max_length=255)
    forum = models.ForeignKey('Forum')
    created = models.DateTimeField(default=datetime.datetime.now,
                                   db_index=True)
    creator = models.ForeignKey(User)
    last_post = models.ForeignKey('Post', related_name='last_post_in',
                                  null=True)
    replies = models.IntegerField(default=0)
    is_locked = models.BooleanField(default=False)
    is_sticky = models.BooleanField(default=False, db_index=True)

    class Meta:
        ordering = ['-is_sticky', '-last_post__created']

    def __setattr__(self, attr, val):
        """Notice when the forum field changes.

        A property won't do here, because it usurps the "forum" name and
        prevents us from using lookups like Thread.objects.filter(forum=f).

        """
        # When http://code.djangoproject.com/ticket/3148 adds nice getter and
        # setter hooks, use those instead.
        if attr == 'forum' and not hasattr(self, '_old_forum'):
            try:
                old = self.forum
            except AttributeError:  # When making a new Thread(forum=3), the
                pass                # forum attr doesn't exist yet.
            else:
                self._old_forum = old
        super(Thread, self).__setattr__(attr, val)

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
            forum.update_last_post(exclude_thread=self)
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

    def save(self, *args, **kwargs):
        super(Thread, self).save(*args, **kwargs)
        old_forum = getattr(self, '_old_forum', None)
        new_forum = self.forum
        if old_forum and old_forum != new_forum:
            old_forum.update_last_post(exclude_thread=self)
            old_forum.save()
            new_forum.update_last_post()
            new_forum.save()
            del self._old_forum

    def update_last_post(self, exclude_post=None):
        """Set my last post to the newest, excluding the given post."""
        last = _last_post_from(self.post_set, exclude_post=exclude_post)
        if last:
            self.last_post = last
        # Otherwise, I have no posts. We leave the reference to the nonexistent
        # or unrelated post in place, which causes Django to automatically
        # delete me.


class Post(ModelBase):
    thread = models.ForeignKey('Thread')
    content = models.TextField()
    author = models.ForeignKey(User)
    created = models.DateTimeField(default=datetime.datetime.now,
                                   db_index=True)
    updated = models.DateTimeField(default=datetime.datetime.now,
                                   db_index=True)
    updated_by = models.ForeignKey(User,
                                   related_name='post_last_updated_by',
                                   null=True)

    class Meta:
        ordering = ['created']

    def __unicode__(self):
        return self.content[:50]

    def save(self, *args, **kwargs):
        """
        Override save method to update parent thread info and take care of
        created and updated.
        """
        new = self.id is None

        if not new:
            self.updated = datetime.datetime.now()

        super(Post, self).save(*args, **kwargs)

        if new:
            self.thread.replies = self.thread.post_set.count() - 1
            self.thread.last_post = self
            self.thread.save()

            self.thread.forum.last_post = self
            self.thread.forum.save()

    def delete(self, *args, **kwargs):
        """Override delete method to update parent thread info."""
        thread = Thread.uncached.get(pk=self.thread.id)
        if thread.last_post_id and thread.last_post_id == self.id:
            thread.update_last_post(exclude_post=self)
        thread.replies = thread.post_set.count() - 2
        thread.save()

        forum = Forum.uncached.get(pk=thread.forum.id)
        if forum.last_post_id and forum.last_post_id == self.id:
            forum.update_last_post(exclude_post=self)
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

        url_ = self.thread.get_absolute_url()
        return urlparams(url_, hash='post-%s' % self.id, **query)

    @property
    def content_parsed(self):
        return wiki_to_html(self.content)
