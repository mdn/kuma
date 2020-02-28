from django.urls import re_path

from . import views

lang_base_urlpatterns = [
    re_path(r"^$", views.search, name="search"),
    re_path(r"^.(?P<format>json)$", views.SearchRedirectView.as_view()),
]


lang_urlpatterns = [
    re_path(r"^xml$", views.plugin, name="search.plugin"),
]
