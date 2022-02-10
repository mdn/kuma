from django.urls import path

from kuma.api.v1.api import admin_api
from kuma.api.v1.plus.notifications import admin_router

admin_api.add_router("/", admin_router)

urlpatterns = [
    path("", admin_api.urls),
]
