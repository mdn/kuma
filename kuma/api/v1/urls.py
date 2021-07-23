from django.urls import path

from . import plus, search, views

urlpatterns = [
    path("whoami", views.whoami, name="api.v1.whoami"),
    path("settings", views.account_settings, name="api.v1.settings"),
    path("search/<locale>", search.search, name="api.v1.search_legacy"),
    path("search", search.search, name="api.v1.search"),
    path(
        "plus/landing-page/survey/",
        plus.landing_page_survey,
        name="api.v1.plus.landing_page_survey",
    ),
]
