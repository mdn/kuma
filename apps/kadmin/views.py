from django import http
from django.contrib import admin
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.views import debug

import jinja2


@admin.site.admin_view
def settings(request):
    """Admin view that displays the django settings."""
    settings = debug.get_safe_settings()
    sorted_settings = [{'key': key, 'value': settings[key]}
                       for key in sorted(settings.keys())]

    return render_to_response('kadmin/settings.html',
                              {'settings': sorted_settings},
                              RequestContext(request, {}))


@admin.site.admin_view
def env(request):
    """Admin view that displays the wsgi env."""
    return http.HttpResponse(u'<pre>%s</pre>' % (jinja2.escape(request)))
