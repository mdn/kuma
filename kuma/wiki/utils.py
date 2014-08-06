from django.conf import settings


def locale_and_slug_from_path(path, request=None, path_locale=None):
    """Given a proposed doc path, try to see if there's a legacy MindTouch
    locale or even a modern Kuma domain in the path. If so, signal for a
    redirect to a more canonical path. In any case, produce a locale and
    slug derived from the given path."""
    locale, slug, needs_redirect = '', path, False
    mdn_languages_lower = dict((x.lower(), x)
                               for x in settings.MDN_LANGUAGES)

    # If there's a slash in the path, then the first segment could be a
    # locale. And, that locale could even be a legacy MindTouch locale.
    if '/' in path:
        maybe_locale, maybe_slug = path.split('/', 1)
        l_locale = maybe_locale.lower()

        if l_locale in settings.MT_TO_KUMA_LOCALE_MAP:
            # The first segment looks like a MindTouch locale, remap it.
            needs_redirect = True
            locale = settings.MT_TO_KUMA_LOCALE_MAP[l_locale]
            slug = maybe_slug

        elif l_locale in mdn_languages_lower:
            # The first segment looks like an MDN locale, redirect.
            needs_redirect = True
            locale = mdn_languages_lower[l_locale]
            slug = maybe_slug

    # No locale yet? Try the locale detected by the request or in path
    if locale == '':
        if request:
            locale = request.locale
        elif path_locale:
            locale = path_locale

    # Still no locale? Probably no request. Go with the site default.
    if locale == '':
        locale = getattr(settings, 'WIKI_DEFAULT_LANGUAGE', 'en-US')

    return (locale, slug, needs_redirect)
