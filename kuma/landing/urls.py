from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.home,
        name='home'),
    url(r'^fellowship/?$',
        views.fellowship,
        name='fellowship'),
    url(r'^promote/?$',
        views.promote_buttons,
        name='promote'),
    url(r'^promote/buttons/?$',
        views.promote_buttons,
        name='promote_buttons'),
    url(r'^contribute\.json$',
        views.contribute_json,
        name='contribute_json'),
    url(r'^maintenance-mode/?$',
        views.maintenance_mode,
        name='maintenance_mode'),
]
