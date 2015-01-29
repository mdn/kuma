import re
from decimal import Decimal

from django.conf import settings
from django.utils.encoding import force_text
from django.utils.formats import number_format

from jingo import register


@register.inclusion_tag('landing/newsfeed.html')
def newsfeed(entries, section_headers=False):
    """Landing page news feed."""
    return {'updates': entries, 'section_headers': section_headers}
