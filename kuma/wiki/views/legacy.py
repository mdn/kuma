# -*- coding: utf-8 -*-
from django.conf import settings
from django.http import Http404
from django.shortcuts import redirect

from ..models import Document, Revision


# Legacy MindTouch redirects.

MINDTOUCH_NAMESPACES = (
    'Help',
    'Help_talk',
    'Project',
    'Project_talk',
    'Special',
    'Talk',
    'Template',
    'Template_talk',
    'User',
)

MINDTOUCH_PROBLEM_LOCALES = {
    'cn': 'zh-CN',
    'en': 'en-US',
    'zh_cn': 'zh-CN',
    'zh_tw': 'zh-TW',
}


def mindtouch_namespace_redirect(request, namespace, slug):
    """
    For URLs in special namespaces (like Talk:, User:, etc.), redirect
    if possible to the appropriate new URL in the appropriate
    locale. If the locale cannot be correctly determined, fall back to
    en-US.
    """
    new_locale = new_slug = None
    if namespace in ('Talk', 'Project', 'Project_talk'):
        # These namespaces carry the old locale in their URL, which
        # simplifies figuring out where to send them.
        locale, _, doc_slug = slug.partition('/')
        new_locale = settings.MT_TO_KUMA_LOCALE_MAP.get(locale, 'en-US')
        new_slug = '%s:%s' % (namespace, doc_slug)
    elif namespace == 'User':
        # For users, we look up the latest revision and get the locale
        # from there.
        new_slug = '%s:%s' % (namespace, slug)
        try:
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
        new_url = '/%s/docs/%s' % (request.LANGUAGE_CODE, new_slug)
    return redirect(new_url, permanent=True)


def mindtouch_to_kuma_redirect(request, path):
    """
    Given a request to a Mindtouch-generated URL, generate a redirect
    to the correct corresponding kuma URL.
    """
    new_locale = None
    if path.startswith('Template:MindTouch'):
        # MindTouch's default templates. There shouldn't be links to
        # them anywhere in the wild, but just in case we 404 them.
        raise Http404

    if path.endswith('/'):
        # If there's a trailing slash, snip it off.
        path = path[:-1]

    if ':' in path:
        namespace, _, slug = path.partition(':')
        # The namespaces (Talk:, User:, etc.) get their own
        # special-case handling.
        if namespace in MINDTOUCH_NAMESPACES:
            return mindtouch_namespace_redirect(request, namespace, slug)

    if '/' in path:
        maybe_locale, _, slug = path.partition('/')
        # There are three problematic locales that MindTouch had which
        # can still be in the path we see after the locale
        # middleware's done its bit. Since those are easy, we check
        # them first.
        if maybe_locale in MINDTOUCH_PROBLEM_LOCALES:
            new_locale = MINDTOUCH_PROBLEM_LOCALES[maybe_locale]
            # We do not preserve UI locale here -- these locales won't
            # be picked up correctly by the locale middleware, and
            # anyone trying to view the document in its locale with
            # their own UI locale will have the correct starting URL
            # anyway.
            new_url = '/%s/docs/%s' % (new_locale, slug)
            if 'view' in request.GET:
                new_url = '%s$%s' % (new_url, request.GET['view'])
            return redirect(new_url, permanent=True)

        # Next we try looking up a Document with the possible locale
        # we've pulled out.
        try:
            doc = Document.objects.get(slug=slug, locale=maybe_locale)
        except Document.DoesNotExist:
            pass

    # Last attempt: we try the request locale as the document locale,
    # and see if that matches something.
    try:
        doc = Document.objects.get(slug=path, locale=request.LANGUAGE_CODE)
    except Document.DoesNotExist:
        raise Http404

    location = doc.get_absolute_url()
    if 'view' in request.GET:
        location = '%s$%s' % (location, request.GET['view'])

    return redirect(location, permanent=True)
