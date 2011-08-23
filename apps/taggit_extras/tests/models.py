from django.db import models

from taggit.managers import TaggableManager
from taggit_extras.managers import NamespacedTaggableManager
from taggit.models import (TaggedItemBase, GenericTaggedItemBase, TaggedItem,
    TagBase, Tag)


class Food(models.Model):
    name = models.CharField(max_length=50)
    tags = NamespacedTaggableManager()

    def __unicode__(self):
        return self.name
