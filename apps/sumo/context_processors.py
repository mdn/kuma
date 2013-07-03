# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf import settings

from wiki.models import OPERATING_SYSTEMS, FIREFOX_VERSIONS


def global_settings(request):
    """Adds settings to the context."""
    return {'settings': settings}


def for_data(request):
    os = dict([(o.slug, o.id) for o in OPERATING_SYSTEMS])
    version = dict([(v.slug, v.id) for v in FIREFOX_VERSIONS])
    return {'for_os': os, 'for_version': version}
