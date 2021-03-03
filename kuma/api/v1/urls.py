from django.urls import path, re_path

from . import search, views

urlpatterns = [
    re_path(r"^whoami/?$", views.whoami, name="api.v1.whoami"),
    # path("csrf", views.csrf, name="api.v1.csrf"),
    path("settings", views.settings_, name="api.v1.settings"),
    path("search/<locale>", search.search, name="api.v1.search_legacy"),
    path("search", search.search, name="api.v1.search"),
    path(
        "subscriptions/feedback/",
        views.send_subscriptions_feedback,
        name="api.v1.send_subscriptions_feedback",
    ),
    path("subscriptions/", views.subscriptions, name="api.v1.subscriptions"),
    path("stripe_hooks/", views.stripe_hooks, name="api.v1.stripe_hooks"),
    path("user_details/", views.user_details, name="api.v1.user_details"),
    path("sendinblue_hooks/", views.sendinblue_hooks, name="api.v1.sendinblue_hooks"),
]
