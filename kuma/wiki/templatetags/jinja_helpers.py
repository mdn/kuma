from urllib.parse import urlsplit, urlunparse

from django.conf import settings
from django_jinja import library


@library.filter
def absolutify(url):
    """Joins settings.SITE_URL with a URL path."""
    if url.startswith("http"):
        return url

    site = urlsplit(settings.SITE_URL)
    parts = urlsplit(url)
    scheme = site.scheme
    netloc = site.netloc
    path = parts.path
    query = parts.query
    fragment = parts.fragment

    if path == "":
        path = "/"

    return urlunparse([scheme, netloc, path, None, query, fragment])
