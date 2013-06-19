from django.conf.urls import url, patterns

urlpatterns = patterns('l10ndashboard.views',

    url(r'^$', 'index'),

)
