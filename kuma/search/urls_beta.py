from django.conf.urls import url

from . import views

urlpatterns = [
    url(r'^$', views.react_search, name='search')
]
