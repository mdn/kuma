# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf.urls.defaults import *


urlpatterns = patterns('devmo.views',
    url(r'^events/?$', 'events', name='events'),
    url(r'^profiles/(?P<username>[^/]+)/?$', 'profile_view',
        name="devmo_profile_view"),
    url(r'^profiles/(?P<username>[^/]+)/edit$', 'profile_edit',
        name="devmo_profile_edit"),
    url(r'^profile/?$', 'my_profile', name="devmo_my_profile"),
    url(r'^profile/edit/?$', 'my_profile_edit',
        name="devmo_my_profile_edit"),
)
