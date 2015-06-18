from django.conf import settings
from django.db import models

from elasticsearch.exceptions import RequestError

from kuma.wiki.search import WikiDocumentType


class FilterManager(models.Manager):
    use_for_related_fields = True

    def visible_only(self):
        return self.filter(visible=True)


class IndexManager(models.Manager):
    """
    The model manager to implement a couple of useful methods for handling
    search indexes.
    """
    def get_current(self):
        try:
            return (self.filter(promoted=True, populated=True)
                        .order_by('-created_at'))[0]
        except (self.model.DoesNotExist, IndexError, AttributeError):
            fallback_name = settings.ES_INDEXES['default']
            index, created = self.get_or_create(name=fallback_name,
                                                promoted=True)
            return index

    def recreate_index(self, es=None, index=None):
        """Delete index if it's there and creates a new one.

        :arg es: ES to use. By default, this creates a new indexing ES.
        :arg index: The Index object to use.

        """
        cls = WikiDocumentType

        if es is None:
            es = cls.get_connection()
        if index is None:
            index = self.get_current()

        index.delete_if_exists()

        # Simultaneously create the index and the mappings, so live
        # indexing doesn't get a chance to index anything between the two
        # causing ES to infer a possibly bogus mapping (which causes ES to
        # freak out if the inferred mapping is incompatible with the
        # explicit mapping).
        try:
            es.indices.create(index.prefixed_name, body=cls.get_settings())
        except RequestError:
            pass
