from django.urls import path

from . import views

lang_urlpatterns = [
    path("terms/", views.payment_terms, name="payment_terms"),
    path("thank-you/", views.thank_you, name="thank_you"),
    path("management/", views.payment_management, name="payment_management",),
    path("", views.index, name="payments_index"),
]
