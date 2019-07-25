

# Add the signin and signout urls
urlpatterns += [url('users/', include('kuma.users.urls_beta'))]
urlpatterns += i18n_patterns(url('',
                                 decorator_include(never_cache,
                                                   users_lang_urlpatterns)))
