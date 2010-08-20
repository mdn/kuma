import datetime

from django.db import models
from django.contrib.auth.models import User

from access import has_perm, perm_is_defined_on
from sumo.helpers import urlparams
from sumo.urlresolvers import reverse
from sumo.models import ModelBase
from sumo.utils import wiki_to_html
from notifications.tasks import delete_watches
import forums


class ThreadLockedError(Exception):
    """Trying to create a post in a locked thread."""


class Forum(ModelBase):
    id = models.AutoField(primary_key=True)
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
        if exclude_post:
            posts = posts.exclude(id=exclude_post.id)
        posts = posts.order_by('-created')
        try:
            last = posts[0]
        except IndexError:
            self.last_post = None
        else:
            self.last_post = last


class Thread(ModelBase):
    id = models.AutoField(primary_key=True)
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

        delete_watches.delay(Thread, self.pk)

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

    def update_last_post(self, exclude_post=None):
        """Set my last post to the newest, excluding `exclude_post`."""
        posts = self.post_set
        if exclude_post:
            posts = posts.exclude(id=exclude_post.id)
        posts = posts.order_by('-created')
        try:
            last = posts[0]
        except IndexError:
            pass  # Threads must have at least 1 post. Thread will be deleted.
        else:
            self.last_post = last


class Post(ModelBase):
    id = models.AutoField(primary_key=True)
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

        url_ = reverse('forums.posts',
                       kwargs={'forum_slug': self.thread.forum.slug,
                               'thread_id': self.thread.id})
        return urlparams(url_, hash='post-%s' % self.id, **query)

    @property
    def content_parsed(self):
        return wiki_to_html(self.content)
