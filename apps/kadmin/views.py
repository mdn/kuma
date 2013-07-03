# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

import re

from django import http
from django.contrib import admin
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views import debug

import celery.conf
import jinja2


@admin.site.admin_view
def settings(request):
    """Admin view that displays the django settings."""
    settings = debug.get_safe_settings()
    sorted_settings = [{'key': key, 'value': settings[key]} for
                       key in sorted(settings.keys())]

    return render_to_response('kadmin/settings.html',
                              {'settings': sorted_settings},
                              RequestContext(request, {}))


@admin.site.admin_view
def celery_settings(request):
    """Admin view that displays the celery configuration."""
    capital = re.compile('^[A-Z]')
    settings = [key for key in dir(celery.conf) if capital.match(key)]
    sorted_settings = [{'key': key, 'value': '*****' if 'password' in
                        key.lower() else getattr(celery.conf, key)} for
                       key in sorted(settings)]

    return render_to_response('kadmin/settings.html',
                              {'settings': sorted_settings},
                              RequestContext(request, {}))


@admin.site.admin_view
def env(request):
    """Admin view that displays the wsgi env."""
    return http.HttpResponse(u'<pre>%s</pre>' % (jinja2.escape(request)))
