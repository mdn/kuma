from redirect_urls import redirect

# Redirects/rewrites/aliases migrated from SCL3 httpd config
redirectpatterns = [
      # RewriteRule ^/media/(redesign/)?css/(.*)-min.css$ /static/build/styles/$2.css [L,R=301]
      redirect(r'^media/(?:redesign/)?css/(?P<doc>.*)-min.css$',
                '/static/build/styles/{doc}.css',
                permanent=True),

      # RewriteRule ^/media/(redesign/)?js/(.*)-min.js$ /static/build/js/$2.js [L,R=301]
      redirect(r'^media/(?:redesign/)?js/(?P<doc>.*)-min.js$',
                '/static/build/js/{doc}.js',
                permanent=True),

      # RewriteRule ^/media/(redesign/)?img(.*) /static/img$2 [L,R=301]
      redirect(r'^media/(?:redesign/)?img(?P<suffix>.*)$',
                '/static/img{suffix}',
                permanent=True),

      # RewriteRule ^/media/(redesign/)?css(.*) /static/styles$2 [L,R=301]
      redirect(r'^media/(?:redesign/)?css(?P<suffix>.*)$',
                '/static/styles{suffix}',
                permanent=True),

      # RewriteRule ^/media/(redesign/)?js(.*) /static/js$2 [L,R=301]
      redirect(r'^media/(?:redesign/)?js(?P<suffix>.*)$',
                '/static/js{suffix}',
                permanent=True),

      # RewriteRule ^/media/(redesign/)?fonts(.*) /static/fonts$2 [L,R=301]
      redirect(r'^media/(?:redesign/)?fonts(?P<suffix>.*)$',
                '/static/fonts{suffix}',
                permanent=True),

      # RedirectMatch 302 /media/uploads/demos/(.*)$ https://developer.mozilla.org/docs/Web/Demos_of_open_web_technologies/
      redirect(r'^media/uploads/demos/(?:.*)$',
                'https://developer.mozilla.org/docs/Web/Demos_of_open_web_technologies/'),

      # RewriteRule ^(.*)//(.*)$ $1_$2 [R=301,L,NC]
      redirect(r'^(?P<one>.*)//(?P<two>.*)$',
                '{one}_{two}',
                permanent=True),

      # RewriteRule ^(.*)//(.*)//(.*)$ $1_$2_$3 [R=301,L,NC]
      redirect(r'^(?P<one>.*)//(?P<two>.*)//(?P<three>.*)$',
                '{one}_{two}_{three}',
                permanent=True),
]
