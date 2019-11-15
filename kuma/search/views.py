from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.generic import RedirectView
from elasticsearch.exceptions import RequestError
from ratelimit.decorators import ratelimit

from kuma.api.v1.views import search as search_api
from kuma.core.decorators import shared_cache_control
from kuma.core.utils import is_wiki

from .search import SearchView

# Since the search endpoint accepts user input (via query parameters) and its
# response is compressed, use rate limiting to mitigate the BREACH attack
# (see http://breachattack.com/). It still needs to allow a user to click
# the filter switches (bug 1426968).
# Alternate: forbid gzip by setting Content-Encoding: identity
@never_cache
@require_GET
@ratelimit(key='user_or_ip', rate='25/m', block=True)
def search(request, *args, **kwargs):
    """
    The search view.
    """
    if is_wiki(request):
        return wiki_search(request, *args, **kwargs)

    results = search_api(request, *args, **kwargs).data
    q = results.get('q')
    has_error = True if results.get('error') else False
    send_results = True if not has_error and q is None else False
    send_error = True if not has_error and q else False
    status = 200 if send_results else 400

    context = {
        'results': {
            'results': results if send_results else None,
            'error': q.get('error') if send_error else None
        }
    }

    return render(request, 'search/react.html', context, status=status)


wiki_search = SearchView.as_view()


class SearchRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        query_string = self.request.META.get('QUERY_STRING')
        url = reverse_lazy('api.v1.search', kwargs={'locale': self.request.LANGUAGE_CODE})
        if query_string:
            url += '?' + query_string
        return url


@shared_cache_control(s_maxage=60 * 60 * 24 * 7)
def plugin(request):
    """Render an OpenSearch Plugin."""
    return render(request, 'search/plugin.html', {
        'locale': request.LANGUAGE_CODE
    }, content_type='application/opensearchdescription+xml')
