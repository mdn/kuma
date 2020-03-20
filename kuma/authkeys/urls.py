from django.urls import re_path

from . import views

urlpatterns = [
    re_path(r"^new$", views.new, name="authkeys.new"),
    re_path(r"^(?P<pk>\d+)/history$", views.history, name="authkeys.history"),
    re_path(r"^(?P<pk>\d+)/delete$", views.delete, name="authkeys.delete"),
]
