from django.conf.urls import url

from . import views
from .views import SearchRedirectView

lang_base_urlpatterns = [
    url(r'^$', views.search, name='search'),
    url(r'^.(?P<format>json)$', SearchRedirectView.as_view())
]


lang_urlpatterns = [
    url(r'^xml$',
        views.plugin,
        name='search.plugin'),
]
