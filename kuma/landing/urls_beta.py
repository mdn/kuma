from __future__ import unicode_literals

from django.conf.urls import url

from kuma.core.decorators import beta_shared_cache_control, shared_cache_control

from . import views


MONTH = 60 * 60 * 24 * 30


lang_urlpatterns = [
    url(r'^$', views.react_home, name='home'),
]

urlpatterns = [
    url(r'^contribute\.json$',
        beta_shared_cache_control(views.contribute_json),
        name='contribute_json'),
    url(r'^robots.txt$',
        beta_shared_cache_control(views.robots_txt),
        name='robots_txt'),
    url(r'^favicon.ico$',
        shared_cache_control(views.FaviconRedirect.as_view(), s_maxage=MONTH),
        name='favicon_ico'),
]
