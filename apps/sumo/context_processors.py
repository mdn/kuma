from django.conf import settings

from wiki.models import OPERATING_SYSTEMS, FIREFOX_VERSIONS


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}


def for_data(request):
    os = dict([(o.slug, o.id) for o in OPERATING_SYSTEMS])
    version = dict([(v.slug, v.id) for v in FIREFOX_VERSIONS])
    return {'for_os': os, 'for_version': version}
