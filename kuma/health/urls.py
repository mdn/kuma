from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^healthz/?$',
        views.liveness,
        name='health.liveness'),
    url(r'^readiness/?$',
        views.readiness,
        name='health.readiness'),
]
