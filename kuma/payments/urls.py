from django.urls import re_path

from . import views

lang_urlpatterns = [
    re_path(r"^terms/$", views.payment_terms, name="payment_terms"),
    re_path(r"^thank-you/$", views.thank_you, name="thank_you"),
    re_path(
        r"^recurring/management/$",
        views.recurring_payment_management,
        name="recurring_payment_management",
    ),
    re_path(r"", views.index, name="payments_index"),
]
