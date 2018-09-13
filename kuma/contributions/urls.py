from django.conf.urls import url

from . import views

lang_urlpatterns = [
    url(r'^confirmation/success/?$',
        views.contribute_confirmation, {'status': 'succeeded'},
        name='contribute_confirmation_succeeded'),
    url(r'^confirmation/error/?$',
        views.contribute_confirmation, {'status': 'error'},
        name='contribute_confirmation_error')
]
