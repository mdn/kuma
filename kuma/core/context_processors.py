from urllib.parse import urlparse

from constance import config
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

    # TODO: Ideally, GOOGLE_ANALYTICS_ACCOUNT is only set in settings (from
    # an environment variable) but for safe transition, we rely on
    # constance if it hasn't been put into settings yet.
    # Once we know with confidence, that GOOGLE_ANALYTICS_ACCOUNT is set
    # and a valid value in the environment (for production!) then we
    # can delete these lines of code.
    # See https://bugzilla.mozilla.org/show_bug.cgi?id=1570076
    google_analytics_account = getattr(settings, "GOOGLE_ANALYTICS_ACCOUNT", None)
    if google_analytics_account is None:
        if config.GOOGLE_ANALYTICS_ACCOUNT != "0":
            settings.GOOGLE_ANALYTICS_ACCOUNT = config.GOOGLE_ANALYTICS_ACCOUNT

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
    if (
        hasattr(request, "path")
        and "login" not in request.path
        and "register" not in request.path
    ):
        return {"next_url": request.get_full_path()}
    return {}
