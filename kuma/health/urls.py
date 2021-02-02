from django.urls import re_path

from . import views


urlpatterns = [
    re_path(r"^healthz/?$", views.liveness, name="health.liveness"),
    re_path(r"^readiness/?$", views.readiness, name="health.readiness"),
    re_path(r"^_kuma_status.json$", views.status, name="health.status"),
]
