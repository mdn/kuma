from __future__ import unicode_literals

from django.conf.urls import url
from django.views.generic.base import RedirectView

from kuma.core.decorators import shared_cache_control

from . import views


WEEK = 60 * 60 * 24 * 7


lang_urlpatterns = [
    url(r'^revisions$',
        views.revisions,
        name='dashboards.revisions'),
    url(r'^user_lookup$',
        views.user_lookup,
        name='dashboards.user_lookup'),
    url(r'^topic_lookup$',
        views.topic_lookup,
        name='dashboards.topic_lookup'),
    url(r'^localization$',
        shared_cache_control(s_maxage=WEEK)(RedirectView.as_view(
            url='/docs/MDN/Doc_status/Overview',
            permanent=True,
        ))),
    url(r'^spam$',
        views.spam,
        name='dashboards.spam'),
    url(r'^macros$',
        views.macros,
        name='dashboards.macros'),
]
