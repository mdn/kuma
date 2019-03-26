from __future__ import unicode_literals

from django.conf.urls import url

from kuma.core.decorators import shared_cache_control

from . import views


lang_urlpatterns = [
    url(r'^$',
        views.react_home,
        name='home'),
]

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
