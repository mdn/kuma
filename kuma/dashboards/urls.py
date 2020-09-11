from django.urls import re_path
from django.views.generic.base import RedirectView

from kuma.core.decorators import shared_cache_control

from . import views


WEEK = 60 * 60 * 24 * 7


lang_urlpatterns = [
    re_path(r"^revisions$", views.revisions, name="dashboards.revisions"),
    re_path(r"^user_lookup$", views.user_lookup, name="dashboards.user_lookup"),
    re_path(r"^topic_lookup$", views.topic_lookup, name="dashboards.topic_lookup"),
    re_path(
        r"^localization$",
        # Here the "shared_cache_control" decorator is an optimization. It
        # informs the CDN to cache the redirect for a week, so once this URL
        # has been requested by a client, all other client requests will be
        # redirected by the CDN instead of this Django service.
        shared_cache_control(s_maxage=WEEK)(
            RedirectView.as_view(
                url="/docs/MDN/Doc_status/Overview",
                permanent=True,
            )
        ),
    ),
    re_path(r"^spam$", views.spam, name="dashboards.spam"),
    re_path(r"^macros$", views.macros, name="dashboards.macros"),
]
