from django.urls import path

from .views import subplat


urlpatterns = [
    path("subplat/subscribe/", subplat.subscribe, name="kuma.users.subplat.subscribe"),
    path("subplat/settings/", subplat.settings_, name="kuma.users.subplat.settings"),
    path("subplat/download/", subplat.download, name="kuma.users.subplat.download"),
]
