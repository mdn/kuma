from django.conf.urls.defaults import *


def exception_raiser(request):
    raise Exception('Raising exception to test logging.')


urlpatterns = patterns('',
                       url(r'^test_exception/$',
                           exception_raiser,
                           name='logging.exception_raiser')
)
