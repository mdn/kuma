# -*- coding: utf-8 -*-
from datetime import datetime

import newrelic.agent

from kuma.core.cache import memcache

from ..constants import DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL
from ..models import Document


def split_slug(slug):
    """
    Utility function to do basic slug splitting
    """
    slug_split = slug.split('/')
    length = len(slug_split)
    root = None

    seo_root = ''
    bad_seo_roots = ['Web']

    if length > 1:
        root = slug_split[0]

        if root in bad_seo_roots:
            if length > 2:
                seo_root = root + '/' + slug_split[1]
        else:
            seo_root = root

    specific = slug_split.pop()

    parent = '/'.join(slug_split)

    return {                         # with this given: "some/kind/of/Path"
        'specific': specific,        # 'Path'
        'parent': parent,            # 'some/kind/of'
        'full': slug,                # 'some/kind/of/Path'
        'parent_split': slug_split,  # ['some', 'kind', 'of']
        'length': length,            # 4
        'root': root,                # 'some'
        'seo_root': seo_root,        # 'some'
    }


@newrelic.agent.function_trace()
def document_last_modified(request, document_slug, document_locale):
    """
    Utility function to derive the last modified timestamp of a document.
    Mainly for the @condition decorator.
    """
    # build an adhoc natural cache key to not have to do DB query
    adhoc_natural_key = (document_locale, document_slug)
    natural_key_hash = Document.natural_key_hash(adhoc_natural_key)
    cache_key = DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL % natural_key_hash
    try:
        last_mod = memcache.get(cache_key)
        if last_mod is None:
            doc = Document.objects.get(locale=document_locale,
                                       slug=document_slug)
            last_mod = doc.fill_last_modified_cache()

        # Convert the cached Unix epoch seconds back to Python datetime
        return datetime.fromtimestamp(float(last_mod))

    except Document.DoesNotExist:
        return None


def document_form_initial(document):
    """
    Return a dict with the document data pertinent for the form.
    """
    return {
        'title': document.title,
        'slug': document.slug,
        'is_localizable': document.is_localizable,
        'tags': list(document.tags.names())
    }
