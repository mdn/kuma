from datetime import datetime

from django.conf import settings
from django.template import defaultfilters

from jingo import register
import pytz


@register.filter
def utctimesince(time):
    return defaultfilters.timesince(time, datetime.utcnow())


def _append_tz(t):
    tz = pytz.timezone(settings.TIME_ZONE)
    return tz.localize(t)


@register.filter
def isotime(t):
    """Date/Time format according to ISO 8601"""
    if not hasattr(t, 'tzinfo'):
        return
    return _append_tz(t).astimezone(pytz.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
