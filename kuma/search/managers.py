from django.conf import settings
from django.db import models


class FilterManager(models.Manager):
    def visible_only(self):
        return self.filter(visible=True)

    def default_filters(self):
        """
        Return default filters as a list of lists of the form::

            [[<group_slug>, <filter_slug>], ...]

        Converting to lists of lists so we can json encode it.

        """
        return [
            list(f)
            for f in self.filter(default=True).values_list(
                "group__slug", "slug", "shortcut"
            )
        ]


class IndexManager(models.Manager):
    """
    The model manager to implement a couple of useful methods for handling
    search indexes.
    """

    def get_current(self):
        try:
            return (self.filter(promoted=True, populated=True).order_by("-created_at"))[
                0
            ]
        except (self.model.DoesNotExist, IndexError, AttributeError):
            fallback_name = settings.ES_INDEXES["default"]
            index, created = self.get_or_create(name=fallback_name, promoted=True)
            return index

    def recreate_index(self, es=None, index=None):
        """Delete index if it's there and creates a new one.

        :arg es: ES to use. By default, this creates a new indexing ES.
        :arg index: The Index object to use.

        """
        raise NotImplementedError
