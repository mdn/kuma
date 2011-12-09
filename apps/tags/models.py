from django.db import models

from south.modelsinspector import add_ignored_fields
from taggit.managers import TaggableManager

from tags.forms import TagField


class BigVocabTaggableManager(TaggableManager):
    """TaggableManager for choosing among a predetermined set of tags

    Taggit's seems hard-coupled to taggit's own plain-text-input widget.

    """
    def formfield(self, form_class=TagField, **kwargs):
        """Swap in our custom TagField."""
        return super(BigVocabTaggableManager, self).formfield(form_class,
                                                              **kwargs)


class BigVocabTaggableMixin(models.Model):
    """Mixin for taggable models that still allows a caching manager to be the
    default manager

    Mix this in after [your caching] ModelBase.

    """
    tags = BigVocabTaggableManager()

    class Meta:
        abstract = True

add_ignored_fields(["tags\.models\.BigVocabTaggableManager"])
