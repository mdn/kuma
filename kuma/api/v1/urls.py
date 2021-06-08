from django.urls import path, re_path

from . import plus, search, views

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
        plus.landing_page_variant,
        name="api.v1.plus.landing_page_variant",
    ),
    path(
        "plus/landing-page/survey/",
        plus.landing_page_survey,
        name="api.v1.plus.landing_page_survey",
    ),
    path("subscriptions/", views.subscriptions, name="api.v1.subscriptions"),
    path("stripe_hooks/", views.stripe_hooks, name="api.v1.stripe_hooks"),
]
