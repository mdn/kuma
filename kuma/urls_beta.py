from django.conf import settings
from django.conf.urls import include, url

from kuma.core import views as core_views
from kuma.core.urlresolvers import i18n_patterns
from kuma.landing.urls_beta import lang_urlpatterns as landing_lang_urlpatterns

handler403 = core_views.handler403
handler404 = core_views.handler404
handler500 = core_views.handler500


urlpatterns = [
    url('^api/', include('kuma.api.urls')),
    # The non-locale-based landing URL's
    url('', include('kuma.landing.urls_beta')),
]
# The locale-based landing URL's
urlpatterns += i18n_patterns(url('', include(landing_lang_urlpatterns)))
# The beta docs URL's (all of which are locale-based)
urlpatterns += i18n_patterns(url(r'^docs/', include('kuma.wiki.urls_beta')))

if getattr(settings, 'DEBUG_TOOLBAR_INSTALLED', False):
    import debug_toolbar
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
