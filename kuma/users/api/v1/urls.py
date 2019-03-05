from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^whoami/?$', views.whoami, name='users.api.whoami'),
]
