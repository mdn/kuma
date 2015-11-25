from django.conf.urls import url
from django.views.generic.base import RedirectView

from . import views


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
        RedirectView.as_view(
            url='/docs/MDN/Doc_status/Overview')),
]
