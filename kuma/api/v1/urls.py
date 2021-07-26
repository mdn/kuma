from django.urls import path

from . import search, views
from .plus import bookmarks, landing_page


urlpatterns = [
    path("whoami", views.whoami, name="api.v1.whoami"),
    path("settings", views.account_settings, name="api.v1.settings"),
    path("search/<locale>", search.search, name="api.v1.search_legacy"),
    path("search", search.search, name="api.v1.search"),
    path(
        "plus/landing-page/survey/",
        landing_page.survey,
        name="api.v1.plus.landing_page.survey",
    ),
    path(
        "plus/bookmarks/bookmarked/",
        bookmarks.bookmarked,
        name="api.v1.plus.bookmarks.bookmarked",
    ),
    path(
        "plus/bookmarks/",
        bookmarks.bookmarks,
        name="api.v1.plus.bookmarks.all",
    ),
]
