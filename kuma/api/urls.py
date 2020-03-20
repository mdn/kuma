from django.urls import include, re_path


urlpatterns = [
    re_path("^v1/", include("kuma.api.v1.urls")),
]
