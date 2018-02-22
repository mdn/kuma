from django.conf.urls import url

from . import views
from kuma.core.decorators import shared_cache_control


urlpatterns = [
    url(r'^$',
        views.home,
        name='home'),
    url(r'^contribute\.json$',
        views.contribute_json,
        name='contribute_json'),
    url(r'^maintenance-mode/?$',
        views.maintenance_mode,
        name='maintenance_mode'),
    url(r'^promote/?$',
        views.promote_buttons,
        name='promote'),
    url(r'^promote/buttons/?$',
        views.promote_buttons,
        name='promote_buttons'),
    url(r'^robots.txt$',
        views.robots_txt,
        name='robots_txt'),
    url(r'^favicon.ico$',
        shared_cache_control(
            views.FaviconRedirect.as_view(icon='favicon.ico')),
        name='favicon_ico'),
]
