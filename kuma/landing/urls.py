from django.urls import re_path

from . import views


urlpatterns = [
    re_path(r"^robots.txt$", views.robots_txt, name="robots_txt"),
]
