from urllib.parse import urlparse

from django.conf import settings
from django.utils import translation

from .i18n import get_language_mapping


def global_settings(request):
    """Adds settings to the context."""

    def clean_safe_url(url):
        if "://" not in url:
            # E.g. 'elasticsearch:9200'
            url = "http://" + url
        parsed = urlparse(url)
        if "@" in parsed.netloc:
            parsed = parsed._replace(
                netloc="username:secret@" + parsed.netloc.split("@")[-1]
            )
        return parsed.geturl()

    return {
        "settings": settings,
        # Because the 'settings.ES_URLS' might contain the username:password
        # it's never appropriate to display in templates. So clean them up.
        # But return it as a lambda so it only executes if really needed.
        "safe_es_urls": lambda: [clean_safe_url(x) for x in settings.ES_URLS],
    }


def i18n(request):
    return {
        "LANGUAGES": get_language_mapping(),
        "LANG": (
            settings.LANGUAGE_URL_MAP.get(translation.get_language())
            or translation.get_language()
        ),
        "DIR": "rtl" if translation.get_language_bidi() else "ltr",
    }


def next_url(request):
    """Return a function by the same name as the context processor.
    That means, in the jinja templates, instead of doing

        {% set url = next_url %}

    you just have to do:

        {% set url = next_url() %}

    which means that the actual context processor function isn't executed
    every single time any jinja template is rendered. Now, only if the
    context processor is actually needed, it gets executed.

    See https://www.peterbe.com/plog/closure-django-context-processors
    """

    def inner():
        if hasattr(request, "path"):
            if request.GET.get("next"):
                # Make a special exception for 'next' URLs that are absolute but
                # who's host is in a known list.
                if (
                    "://" in request.GET["next"]
                    and settings.DEBUG
                    and settings.ADDITIONAL_NEXT_URL_ALLOWED_HOSTS
                    in request.GET["next"]
                ):
                    # The reason we don't need to make a much more elaborate
                    # comparison of the host and the 'ADDITIONAL_NEXT_URL_ALLOWED_HOSTS'
                    # setting is because this will only ever happen in DEBUG anyway.
                    return request.GET["next"]
                if "://" not in request.GET["next"]:
                    return request.GET["next"]
            elif not request.get_full_path().endswith(settings.LOGIN_URL):
                # The only exception is the sign-in landing page which you get to
                # if you can't use the auth modal.
                return request.get_full_path()

    return {"next_url": inner}
