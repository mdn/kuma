from django.urls import path, re_path

from . import search, views
from .plus import bookmarks, landing_page

urlpatterns = [
    re_path(r"^whoami/?$", views.whoami, name="api.v1.whoami"),
    path("settings", views.account_settings, name="api.v1.settings"),
    path("search/<locale>", search.search, name="api.v1.search_legacy"),
    path("search", search.search, name="api.v1.search"),
    path(
        "subscriptions/feedback/",
        views.send_subscriptions_feedback,
        name="api.v1.send_subscriptions_feedback",
    ),
    path(
        "plus/landing-page/variant/",
        landing_page.variant,
        name="api.v1.plus.landing_page.variant",
    ),
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
    path("subscriptions/", views.subscriptions, name="api.v1.subscriptions"),
    path("stripe_hooks/", views.stripe_hooks, name="api.v1.stripe_hooks"),
]
