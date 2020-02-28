from django.urls import re_path

from . import views

lang_urlpatterns = [
    re_path(r"^recurring/?$", views.contribute, name="recurring_payment_initial"),
    re_path(
        r"^recurring/subscription/?$",
        views.contribute,
        name="recurring_payment_subscription",
    ),
    re_path(r"^terms/?$", views.payment_terms, name="payment_terms"),
    re_path(
        r"^recurring/management/?$",
        views.recurring_payment_management,
        name="recurring_payment_management",
    ),
]
