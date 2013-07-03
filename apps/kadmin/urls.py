# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf.urls.defaults import patterns, url, include
from django.contrib import admin

from . import views


urlpatterns = patterns('',
    # Kitsune stuff.
    url('^celery', views.celery_settings, name='kadmin.celery'),
    url('^settings', views.settings, name='kadmin.settings'),
    url('^env$', views.env, name='kadmin.env'),

    # The Django admin.
    url('^', include(admin.site.urls)),
)
