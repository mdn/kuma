from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^persona/signin$',
        views.persona_login,
        name="persona_login"),
    url(r'^persona/complete$',
        views.persona_complete,
        name="persona_complete"),
    url(r'^persona/csrf$',
        views.persona_csrf,
        name="persona_csrf_token"),
]
