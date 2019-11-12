

from django.conf.urls import url

from . import views

lang_urlpatterns = [
    url(r'^recurring/?$',
        views.contribute,
        name='recurring_payment_initial'),
    url(r'^recurring/subscription/?$',
        views.contribute,
        name='recurring_payment_subscription'),
    url(r'^terms/?$',
        views.payment_terms,
        name='payment_terms'),
    url(r'^recurring/management/?$',
        views.recurring_payment_management,
        name='recurring_payment_management'),
]
