from django.urls import path

from . import views

lang_urlpatterns = [
    path("", views.index, name="accountsettings_index"),
]
