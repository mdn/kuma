import urllib2

from django.conf import settings
from django.core.cache import cache

import cronjobs


@cronjobs.register
def get_queue_status():
    """Update the live chat queue status."""

    status_path = '/plugins/fastpath/workgroup-stats?workgroup=support&rand='
    url = settings.CHAT_SERVER + status_path
    xml = urllib2.urlopen(url)
    cache.set(settings.CHAT_CACHE_KEY, xml.read())
