from django.urls import path
from django.views.generic import RedirectView

from . import views

lang_urlpatterns = [
    path("terms/", views.payment_terms, name="payment_terms"),
    path("thank-you/", views.thank_you, name="thank_you"),
    path(
        # This is the old URL we had for a while
        "recurring/management/",
        RedirectView.as_view(pattern_name="payment_management", permanent=True),
        name="recurring_payment_management",
    ),
    path("management/", views.payment_management, name="payment_management"),
    path("", views.index, name="payments_index"),
]
