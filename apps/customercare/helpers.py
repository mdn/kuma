from datetime import datetime

from django.template import defaultfilters

from jingo import register


@register.filter
def utctimesince(time):
    return defaultfilters.timesince(time, datetime.utcnow())
