import hashlib

from urlobject import URLObject as URL

from django.conf import settings
from django.utils import translation

from sumo.urlresolvers import reverse

QUERY_PARAM = 'q'
PAGE_PARAM = 'page'
TOPICS_PARAM = 'topic'


def ref_from_referer(request):
    referrer = request.META.get('HTTP_REFERER', None)
    if (referrer is None or
            reverse('search', locale=request.locale) != URL(referrer).path):
        return None
    return ref_from_url(referrer)


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
        md5.update(unicode(value))

    return md5.hexdigest()[:16]
