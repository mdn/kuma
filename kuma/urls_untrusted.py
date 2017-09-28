from django.conf import settings
from django.conf.urls import include, url


urlpatterns = [
    url('', include('kuma.attachments.urls')),
    url(r'^docs', include('kuma.wiki.urls_untrusted')),
]

if getattr(settings, 'DEBUG_TOOLBAR_INSTALLED', False):
    import debug_toolbar
    urlpatterns.append(
        url(r'^__debug__/', include(debug_toolbar.urls)),
    )
