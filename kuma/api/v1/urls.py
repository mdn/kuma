from django.urls import path, re_path

from . import search, views
from .plus import bookmarks, landing_page, notifications

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
        "plus/bookmarks/",
        bookmarks.bookmarks,
        name="api.v1.plus.bookmarks",
    ),
    path(
        "plus/notifications/",
        notifications.notifications,
        name="api.v1.plus.notifications",
    ),
    path(
        "plus/notifications/<id>/mark-as-read/",
        notifications.mark_as_read,
        name="api.v1.plus.notifications.mark_as_read",
    ),
    path(
        "plus/notifications/all/mark-as-read/",
        notifications.mark_as_read,
        name="api.v1.plus.notifications.mark_all_as_read",
    ),
    path(
        "plus/notifications/create/",
        notifications.create,
        name="api.v1.plus.notifications.create",
    ),
    path(
        "plus/watched/",
        notifications.watched,
        name="api.v1.plus.notifications.watched",
    ),
    re_path(
        "plus/watch(?P<url>/.+)",
        notifications.watch,
        name="api.v1.plus.notifications.watch",
    ),
]
