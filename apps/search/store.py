import hashlib

from urlobject import URLObject as URL

from django.utils import translation
from django.utils.encoding import smart_str

from sumo.urlresolvers import reverse

QUERY_PARAM = 'q'
PAGE_PARAM = 'page'
TOPICS_PARAM = 'topic'


def referrer_url(request):
    referrer = request.META.get('HTTP_REFERER', None)
    if (referrer is None or
            reverse('search', locale=request.locale) != URL(referrer).path):
        return None
    return referrer


def ref_from_referrer(request):
    return ref_from_url(referrer_url(request))


def ref_from_request(request):
    return ref_from_url(request.build_absolute_uri())


def ref_from_url(url):
    url = URL(url)
    query = url.query.dict.get(QUERY_PARAM, '')
    page = url.query.dict.get(PAGE_PARAM, 1)
    topics = url.query.multi_dict.get(TOPICS_PARAM, [])
    locale = translation.get_language()

    md5 = hashlib.md5()
    for value in [query, page, locale] + topics:
        md5.update(smart_str(value))

    return md5.hexdigest()[:16]
