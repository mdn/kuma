from django.conf import settings
from django.contrib.staticfiles.storage import staticfiles_storage


def favicon_url():
    """Return the path of the basic favicon."""
    if settings.DOMAIN == settings.PRODUCTION_DOMAIN:
        suffix = ""
    elif settings.DOMAIN == settings.STAGING_DOMAIN:
        suffix = "-staging"
    else:
        suffix = "-local"
    return staticfiles_storage.url("img/favicon32%s.png" % suffix)
