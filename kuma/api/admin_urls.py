from django.urls import path

from kuma.api.v1.api import admin_api

urlpatterns = [
    path("", admin_api.urls),
]
