from django.urls import re_path

from kuma.core.decorators import shared_cache_control

from . import views


MONTH = 60 * 60 * 24 * 30


lang_urlpatterns = [
    re_path(r"^$", views.home, name="home"),
    re_path(r"^maintenance-mode/?$", views.maintenance_mode, name="maintenance_mode"),
    re_path(r"^promote/?$", views.promote_buttons, name="promote"),
    re_path(r"^promote/buttons/?$", views.promote_buttons, name="promote_buttons"),
]

urlpatterns = [
    re_path(r"^contribute\.json$", views.contribute_json, name="contribute_json"),
    re_path(r"^robots.txt$", views.robots_txt, name="robots_txt"),
    re_path(
        r"^favicon.ico$",
        shared_cache_control(views.FaviconRedirect.as_view(), s_maxage=MONTH),
        name="favicon_ico",
    ),
]
