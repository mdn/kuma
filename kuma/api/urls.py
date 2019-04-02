from django.conf.urls import include, url


urlpatterns = [
    url('^v1/', include('kuma.api.v1.urls')),
]
