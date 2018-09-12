from django.conf.urls import url
from django.conf import settings

from kuma.core.decorators import shared_cache_control

from . import views


lang_urlpatterns = [
    url(r'^$',
        views.home,
        name='home'),
    url(r'^maintenance-mode/?$',
        views.maintenance_mode,
        name='maintenance_mode'),
    url(r'^promote/?$',
        views.promote_buttons,
        name='promote'),
    url(r'^promote/buttons/?$',
        views.promote_buttons,
        name='promote_buttons'),
]

if settings.MDN_CONTRIBUTION:
    lang_urlpatterns.extend((
        url(r'^contribute/?$',
            views.contribute,
            name='contribute'),
        url(r'^contribute/confirmation/success/?$',
            views.contribute_confirmation, {'status': 'succeeded'},
            name='contribute_confirmation_succeeded'),
        url(r'^contribute/confirmation/error/?$',
            views.contribute_confirmation, {'status': 'error'},
            name='contribute_confirmation_error')
    ))

urlpatterns = [
    url(r'^contribute\.json$',
        views.contribute_json,
        name='contribute_json'),
    url(r'^robots.txt$',
        views.robots_txt,
        name='robots_txt'),
    url(r'^favicon.ico$',
        shared_cache_control(views.FaviconRedirect.as_view()),
        name='favicon_ico'),
]
