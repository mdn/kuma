from django.urls import re_path

from kuma.core.decorators import shared_cache_control

from . import views


MONTH = 60 * 60 * 24 * 30


lang_urlpatterns = [
    re_path(r"^$", views.home, name="home"),
    re_path(r"^maintenance-mode/?$", views.maintenance_mode, name="maintenance_mode"),
]

urlpatterns = [
    re_path(r"^robots.txt$", views.robots_txt, name="robots_txt"),
    re_path(
        r"^favicon.ico$",
        shared_cache_control(views.FaviconRedirect.as_view(), s_maxage=MONTH),
        name="favicon_ico",
    ),
]
