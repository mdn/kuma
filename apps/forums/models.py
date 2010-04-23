"""
Models for Kitsune discussion forum. If you're looking for the support
forum, then these are not the models you're looking for. You can go about
your business. Move along.
"""

from django.db import models
from django.contrib.auth.models import User

from sumo.urlresolvers import reverse
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
    creator = models.ForeignKey(User, related_name='threads')
    is_locked = models.BooleanField(default=False)

    def __unicode__(self):
        return self.title


class Post(ModelBase):
    id = models.AutoField(primary_key=True)
    thread = models.ForeignKey('Thread')
    content = models.TextField()
    author = models.ForeignKey(User)
    created = models.DateTimeField(auto_now_add=True, db_index=True)
    updated = models.DateTimeField(auto_now=True, db_index=True)
    
    def __unicode__(self):
        return self.content[:50]
