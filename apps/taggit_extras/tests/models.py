# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
