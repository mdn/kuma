# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.conf.urls.defaults import *

urlpatterns = patterns('authkeys.views',
    url(r'^$', 'list', name='authkeys.list'),
    url(r'^new$', 'new', name='authkeys.new'),
    url(r'^(?P<pk>\d+)/history$', 'history', name='authkeys.history'),
    url(r'^(?P<pk>\d+)/delete$', 'delete', name='authkeys.delete'),
)
