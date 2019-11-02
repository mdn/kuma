# -*- coding: utf-8 -*-


from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect

from kuma.core.decorators import shared_cache_control

from ..constants import LEGACY_MINDTOUCH_NAMESPACES
from ..models import Document, Revision


# Legacy MindTouch redirects.

def mindtouch_namespace_to_kuma_url(locale, namespace, slug):
    """
    Convert MindTouch namespace URLs to Kuma URLs.

    For special namespaces like Talk:, User:, etc., convert to the
    approproate new URL, converting MT locales to Kuma locales.
    If the locale cannot be correctly determined, fall back to en-US
    """
    new_locale = new_slug = None
    if namespace in ('Talk', 'Project', 'Project_talk'):
        # These namespaces carry the old locale in their URL, which
        # simplifies figuring out where to send them.
        mt_locale, _, doc_slug = slug.partition('/')
        new_locale = settings.MT_TO_KUMA_LOCALE_MAP.get(mt_locale, 'en-US')
        new_slug = '%s:%s' % (namespace, doc_slug)
    elif namespace == 'User':
        # For users, we look up the latest revision and get the locale
        # from there.
        new_slug = '%s:%s' % (namespace, slug)
        try:
            # TODO: Tests do not include a matching revision
            rev = (Revision.objects.filter(document__slug=new_slug)
                                   .latest('created'))
            new_locale = rev.document.locale
        except Revision.DoesNotExist:
            # If that doesn't work, bail out to en-US.
            new_locale = 'en-US'
    else:
        # Templates, etc. don't actually have a locale, so we give
        # them the default.
        new_locale = 'en-US'
        new_slug = '%s:%s' % (namespace, slug)
    if new_locale:
        # TODO: new_locale is unused, no alternate branch
        new_url = '/%s/docs/%s' % (locale, new_slug)
    return new_url


def mindtouch_to_kuma_url(locale, path):
    """
    Convert valid MindTouch namespace URLs to Kuma URLs.

    If there is an appropriate Kuma URL, then it is returned.
    If there is no appropriate Kuma URL, then None is returned.
    """
    if path.startswith('%s/' % locale):
        # Convert from Django-based LocaleMiddleware path to zamboni/amo style
        path = path.replace('%s/' % locale, '', 1)

    if path.startswith('Template:MindTouch'):
        # MindTouch's default templates. There shouldn't be links to
        # them anywhere in the wild, but just in case we 404 them.
        # TODO: Tests don't exercise this branch
        return None

    if path.endswith('/'):
        # If there's a trailing slash, snip it off.
        path = path[:-1]

    if ':' in path:
        namespace, _, slug = path.partition(':')
        # The namespaces (Talk:, User:, etc.) get their own
        # special-case handling.
        # TODO: Test invalid namespace
        if namespace in LEGACY_MINDTOUCH_NAMESPACES:
            return mindtouch_namespace_to_kuma_url(locale, namespace, slug)

    # Last attempt: we try the request locale as the document locale,
    # and see if that matches something.
    try:
        doc = Document.objects.get(slug=path, locale=locale)
    except Document.DoesNotExist:
        return None

    location = doc.get_absolute_url()
    return location


@shared_cache_control(s_maxage=60 * 60 * 24 * 30)
def mindtouch_to_kuma_redirect(request, path):
    """
    Given a request to a Mindtouch-generated URL, generate a redirect
    to the correct corresponding kuma URL.

    TODO: Retire this catch-all view and Mindtouch redirects.
    Safest: Ensure no current content includes these URLs, no incoming links.
    Middle: Monitor 404s and their referrer headers, fix links after removal.
    Fastest: Remove it, ignore 404s.
    """
    locale = request.LANGUAGE_CODE
    url = mindtouch_to_kuma_url(locale, path)
    if url:
        if 'view' in request.GET:
            url = '%s$%s' % (url, request.GET['view'])
        return redirect(url, permanent=True)
    else:
        raise Http404
