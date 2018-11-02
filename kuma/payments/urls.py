from django.conf.urls import url

from . import views

lang_urlpatterns = [
    url(r'^success/?$',
        views.confirmation, {'status': 'succeeded'},
        name='payment_succeeded'),
    url(r'^error/?$',
        views.confirmation, {'status': 'error'},
        name='payment_error'),
    url(r'^recurring/?$',
        views.contribute_recurring_payment_initial,
        name='recurring_payment_initial'),
    url(r'^recurring/subscription/?$',
        views.contribute_recurring_payment_subscription,
        name='recurring_payment_subscription')
]
