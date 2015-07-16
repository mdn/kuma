import hashlib

from urlobject import URLObject as URL

from django.utils import translation
from django.utils.encoding import smart_str

from kuma.core.urlresolvers import reverse

from .filters import get_filters

QUERY_PARAM = 'q'
PAGE_PARAM = 'page'


def referrer_url(request):
    referrer = request.META.get('HTTP_REFERER', None)

    # Non-ASCII referers can be problematic.
    # TODO: The 'ftfy' library can probably fix these, but may not be
    # worth the effort.
    try:
        urlpath = URL(referrer).path
    except UnicodeDecodeError:
        urlpath = None

    if (referrer is None or urlpath is None or
            reverse('search', locale=request.locale) != urlpath):
        return None
    return referrer


def ref_from_referrer(request):
    return ref_from_url(referrer_url(request))


def ref_from_request(request):
    return ref_from_url(request.build_absolute_uri())


def ref_from_url(url):
    url = URL(url)
    md5 = hashlib.md5()

    try:
        query = url.query.dict.get(QUERY_PARAM, '')
        page = url.query.dict.get(PAGE_PARAM, 1)
        filters = get_filters(url.query.multi_dict.get)
    except UnicodeDecodeError:
        query = ''
        page = 1
        filters = []

    locale = translation.get_language()

    for value in [query, page, locale] + filters:
        md5.update(smart_str(value))

    return md5.hexdigest()[:16]
