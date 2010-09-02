from datetime import datetime

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from sumo.models import ModelBase


class Media(ModelBase):
    """Generic model for media"""
    title = models.CharField(max_length=255, db_index=True)
    created = models.DateTimeField(default=datetime.now, db_index=True)
    updated = models.DateTimeField(default=datetime.now, db_index=True)
    updated_by = models.ForeignKey(User, null=True)
    description = models.TextField(max_length=10000)
    locale = models.CharField(max_length=7, db_index=True,
                              default=settings.GALLERY_DEFAULT_LANGUAGE,
                              choices=settings.LANGUAGE_CHOICES)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.title + ': ' + self.file.name[30:]

    def thumbnail_or_file(self):
        """Returns self.thumbnail, if set, else self.file"""
        return self.thumbnail if self.thumbnail else self.file


class Image(Media):
    creator = models.ForeignKey(User, related_name='gallery_images')
    file = models.ImageField(upload_to=settings.GALLERY_IMAGE_PATH)
    thumbnail = models.ImageField(
        upload_to=settings.GALLERY_IMAGE_THUMBNAIL_PATH, null=True)


class Video(Media):
    creator = models.ForeignKey(User, related_name='gallery_videos')
    file = models.FileField(upload_to=settings.GALLERY_VIDEO_PATH)
    thumbnail = models.ImageField(
        upload_to=settings.GALLERY_VIDEO_THUMBNAIL_PATH, null=True)
