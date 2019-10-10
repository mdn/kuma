from django.shortcuts import render
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
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

    context = {
        'results': {
            'results': search_api(request, *args, **kwargs).data
        }
    }

    return render(request, 'search/react.html', context)


wiki_search = SearchView.as_view()


@shared_cache_control(s_maxage=60 * 60 * 24 * 7)
def plugin(request):
    """Render an OpenSearch Plugin."""
    return render(request, 'search/plugin.html', {
        'locale': request.LANGUAGE_CODE
    }, content_type='application/opensearchdescription+xml')
