from datetime import datetime

from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

from tower import ugettext_lazy as _lazy

from sumo.models import ModelBase
from sumo.urlresolvers import reverse


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


class Image(Media):
    creator = models.ForeignKey(User, related_name='gallery_images')
    file = models.ImageField(upload_to=settings.GALLERY_IMAGE_PATH)
    thumbnail = models.ImageField(
        upload_to=settings.GALLERY_IMAGE_THUMBNAIL_PATH, null=True)

    def get_absolute_url(self):
        return reverse('gallery.media', args=['image', self.id])

    def thumbnail_url_if_set(self):
        """Returns self.thumbnail, if set, else self.file"""
        return self.thumbnail.url if self.thumbnail else self.file.url


class Video(Media):
    creator = models.ForeignKey(User, related_name='gallery_videos')
    webm = models.FileField(upload_to=settings.GALLERY_VIDEO_PATH, null=True)
    ogv = models.FileField(upload_to=settings.GALLERY_VIDEO_PATH, null=True)
    flv = models.FileField(upload_to=settings.GALLERY_VIDEO_PATH, null=True)
    thumbnail = models.ImageField(
        upload_to=settings.GALLERY_VIDEO_THUMBNAIL_PATH, null=True)

    def get_absolute_url(self):
        return reverse('gallery.media', args=['video', self.id])

    def thumbnail_url_if_set(self):
        """Returns self.thumbnail.url, if set, else default thumbnail URL"""
        return self.thumbnail.url if self.thumbnail \
                                  else settings.THUMBNAIL_PROGRESS_URL

    def clean(self):
        """Ensure one of the supported file formats has been uploaded"""
        if not (self.webm or self.ogv or self.flv):
            raise ValidationError(
                _lazy('The video has no files associated with it. You must '
                      'upload one of the following extensions: webm, ogv, '
                      'flv.'))
