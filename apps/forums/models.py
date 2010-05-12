from django.db import models
from django.contrib.auth.models import User

from sumo.models import ModelBase


class Forum(ModelBase):
    id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    slug = models.SlugField(unique=True)

    def __unicode__(self):
        return self.name


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
        return self.replies / 20 + 1

    def __unicode__(self):
        return self.title


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
