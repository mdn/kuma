from django.urls import path

from . import search
from .api import api

urlpatterns = [
    path("", api.urls),
    path("search/<locale>", search.search, name="api.v1.search_legacy"),
    path("search", search.search, name="api.v1.search"),
]
