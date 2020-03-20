import hashlib

from django.contrib.sites.models import Site
from django.utils import translation
from django.utils.encoding import smart_bytes
from urlobject import URLObject as URL

from kuma.core.urlresolvers import reverse

from .filters import get_filters

QUERY_PARAM = "q"
PAGE_PARAM = "page"


def get_search_url_from_referer(request):
    """Returns search url from referer if it was an MDN search"""
    # Note: "HTTP_REFERER" is spelled wrong in the spec and we use "referer"
    # here to mirror that.
    referer = request.META.get("HTTP_REFERER", None)

    # Non-ASCII referers can be problematic.
    # TODO: The 'ftfy' library can probably fix these, but may not be
    # worth the effort.
    try:
        url = URL(referer)
    except UnicodeDecodeError:
        url = None

    current_site = Site.objects.get_current()

    # The referer url must be an MDN search--if not, then we return None.
    # We verify the protocol, host and path.
    if (
        referer is None
        or url is None
        or url.scheme != "https"
        or url.netloc != current_site.domain
        or reverse("search") != url.path
    ):
        return None
    return referer


def ref_from_referrer(request):
    return ref_from_url(get_search_url_from_referer(request))


def ref_from_request(request):
    return ref_from_url(request.build_absolute_uri())


def ref_from_url(url):
    url = URL(url)
    md5 = hashlib.md5()

    try:
        query = url.query.dict.get(QUERY_PARAM, "")
        page = url.query.dict.get(PAGE_PARAM, 1)
        filters = get_filters(url.query.multi_dict.get)
    except UnicodeDecodeError:
        query = ""
        page = 1
        filters = []

    locale = translation.get_language()

    for value in [query, page, locale] + list(filters):
        md5.update(smart_bytes(value))

    return md5.hexdigest()[:16]
