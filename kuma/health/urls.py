from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^healthz/?$',
        views.basic_health,
        name='health.liveness'),
    url(r'^readiness/?$',
        views.basic_health,
        name='health.readiness'),
]
