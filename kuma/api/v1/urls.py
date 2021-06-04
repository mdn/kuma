from django.urls import path, re_path

from . import search, views
from .plus import landing_page, notes

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
        "plus/notes/document/",
        notes.document,
        name="api.v1.plus.notes.document",
    ),
    path("subscriptions/", views.subscriptions, name="api.v1.subscriptions"),
    path("stripe_hooks/", views.stripe_hooks, name="api.v1.stripe_hooks"),
    path("user_details/", views.user_details, name="api.v1.user_details"),
    path("sendinblue_hooks/", views.sendinblue_hooks, name="api.v1.sendinblue_hooks"),
]
