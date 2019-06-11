from decorator_include import decorator_include
from django.conf import settings
from django.conf.urls import include, url
from django.views.decorators.cache import never_cache
from django.views.generic import RedirectView
from django.views.static import serve

from kuma.core import views as core_views
from kuma.core.decorators import beta_shared_cache_control, shared_cache_control
from kuma.core.urlresolvers import i18n_patterns
from kuma.landing.urls_beta import lang_urlpatterns as landing_lang_urlpatterns
from kuma.users.urls_beta import lang_urlpatterns as users_lang_urlpatterns
from kuma.views import serve_from_media_root


handler403 = core_views.handler403
handler404 = core_views.handler404
handler500 = core_views.handler500

DAY = 60 * 60 * 24
MONTH = DAY * 30
YEAR = DAY * 365

redirect_to_attachments_domain = shared_cache_control(
    RedirectView.as_view(url=settings.ATTACHMENT_SITE_URL + '/%(path)s'),
    s_maxage=YEAR
)

urlpatterns = [
    url('', include('kuma.health.urls')),
    url('^api/', include('kuma.api.urls')),
    # The non-locale-based landing URL's
    url('', include('kuma.landing.urls_beta')),
]
# The locale-based landing URL's
urlpatterns += i18n_patterns(url('', include(landing_lang_urlpatterns)))
# The beta docs URL's (all of which are locale-based)
urlpatterns += i18n_patterns(url(r'^docs/', include('kuma.wiki.urls_beta')))
# The version, sitemap, humans, and file-attachment URL's (all non-locale-based)
urlpatterns += [
    url('', include('kuma.version.urls')),
    url(r'^sitemap.xml$', beta_shared_cache_control(serve_from_media_root),
        {'path': 'sitemap.xml'}, name='sitemap'),
    url(r'^(?P<path>sitemaps/.+)$',
        beta_shared_cache_control(serve_from_media_root), name='sitemaps'),
    url(r'^humans.txt$', beta_shared_cache_control(serve),
        {'document_root': settings.HUMANSTXT_ROOT, 'path': 'humans.txt'}),
    # Redirect file attachment URL's to the attachments domain, and
    # let that domain determine whether or not the file exists.
    url(r'^(?P<path>files/.+)$', redirect_to_attachments_domain,
        name='attachments.raw_file'),
    url(r'^(?P<path>@api/deki/files/.+)$', redirect_to_attachments_domain,
        name='attachments.mindtouch_file_redirect'),
]

# Add the signin and signout urls
urlpatterns += [url('users/', include('kuma.users.urls_beta'))]
urlpatterns += i18n_patterns(url('',
                                 decorator_include(never_cache,
                                                   users_lang_urlpatterns)))


if getattr(settings, 'DEBUG_TOOLBAR_INSTALLED', False):
    import debug_toolbar
    urlpatterns.append(url(r'^__debug__/', include(debug_toolbar.urls)))
