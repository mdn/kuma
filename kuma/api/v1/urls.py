from django.urls import path

from . import search, views
from .api import api
from .plus import bookmarks

urlpatterns = [
    path("", api.urls),
    path("whoami", views.whoami, name="api.v1.whoami"),
    path("settings", views.account_settings, name="api.v1.settings"),
    path("search/<locale>", search.search, name="api.v1.search_legacy"),
    path("search", search.search, name="api.v1.search"),
    path(
        "plus/bookmarks/",
        bookmarks.bookmarks,
        name="api.v1.plus.bookmarks",
    ),
]
