from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views
from kuma.core.decorators import shared_cache_control


urlpatterns = [
    url(r'^dashboards/revisions$',
        views.revisions,
        name='dashboards.revisions'),
    url(r'^dashboards/user_lookup$',
        views.user_lookup,
        name='dashboards.user_lookup'),
    url(r'^dashboards/topic_lookup$',
        views.topic_lookup,
        name='dashboards.topic_lookup'),
    url(r'^dashboards/localization$',
        shared_cache_control(RedirectView.as_view(
            url='/docs/MDN/Doc_status/Overview',
            permanent=True,
        ))),
    url(r'^dashboards/spam$',
        views.spam,
        name='dashboards.spam'),
    url(r'^dashboards/macros$',
        views.macros,
        name='dashboards.macros'),
]
