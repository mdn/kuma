from django.conf.urls import url

from . import views

lang_urlpatterns = [
    url(r'^success/?$',
        views.confirmation, {'status': 'succeeded'},
        name='contribute_succeeded'),
    url(r'^error/?$',
        views.confirmation, {'status': 'error'},
        name='contribute_error')
]
