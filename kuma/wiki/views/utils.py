# -*- coding: utf-8 -*-
from datetime import datetime

import newrelic.agent
import waffle

from kuma.core.cache import memcache

from ..constants import DOCUMENT_LAST_MODIFIED_CACHE_KEY_TMPL
from ..events import EditDocumentEvent
from ..models import Document, RevisionIP
from ..tasks import send_first_edit_email


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

    return {
        'specific': specific,
        'parent': parent,
        'full': slug,
        'parent_split': slug_split,
        'length': length,
        'root': root,
        'seo_root': seo_root,
    }


def join_slug(parent_split, slug):
    parent_split.append(slug)
    return '/'.join(parent_split)


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
        'category': document.category,
        'is_localizable': document.is_localizable,
        'tags': list(document.tags.values_list('name', flat=True))
    }


def save_revision_and_notify(rev_form, request, document):
    """
    Save the given RevisionForm and send notifications.
    """
    creator = request.user
    # have to check for first edit before we rev_form.save
    first_edit = creator.wiki_revisions().count() == 0

    new_rev = rev_form.save(creator, document)

    if waffle.switch_is_active('store_revision_ips'):
        ip = request.META.get('REMOTE_ADDR')
        RevisionIP.objects.create(revision=new_rev, ip=ip)

    if first_edit:
        send_first_edit_email.delay(new_rev.pk)

    document.schedule_rendering('max-age=0')

    # Enqueue notifications
    EditDocumentEvent(new_rev).fire(exclude=new_rev.creator)
