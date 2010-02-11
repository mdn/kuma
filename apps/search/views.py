# Create your views here.

from django.conf import settings

import jingo

from sumo.models import ForumThread, WikiPage

from .clients import ForumClient, WikiClient
from .utils import crc32


WHERE_WIKI = 1
WHERE_FORUM = 2
WHERE_ALL = WHERE_WIKI | WHERE_FORUM


def search(request):
    q = request.GET.get('q', 'search')

    locale = (crc32(request.GET.get('locale', request.LANGUAGE_CODE)),)

    where = int(request.GET.get('w', WHERE_ALL))

    offset = int(request.GET.get('offset', 0))

    documents = []

    if (where & WHERE_WIKI):
        wc = WikiClient() # Wiki SearchClient instance
        filters_w = [] # filters for the wiki search

        # Category filter
        filters_w.append({
            'filter': 'category',
            'value': map(int,
                         request.GET.get('category',
                             settings.SEARCH_DEFAULT_CATEGORIES).split(',')),
        })

        # Locale filter
        filters_w.append({
            'filter': 'locale',
            'value': locale,
        })

        # Tag filter
        if request.GET.get('tag') is not None:
            filters_w.append({
                'filter': 'tag',
                'value': map(crc32, request.GET.get('tag').split(',')),
            })

        # execute the query and append to documents
        documents += wc.query(q, filters_w)

    if (where & WHERE_FORUM):
        fc = ForumClient() # Forum SearchClient instance
        filters_f = [] # filters for the forum search

        # Forum filter
        filters_f.append({
            'filter': 'forumId',
            'value': map(int,
                          request.GET.get('forums',
                              settings.SEARCH_DEFAULT_FORUM).split(',')),
        })

        # Status filter
        if request.GET.get('status') is not None:
            filters_f.append({
                'filter': 'status',
                'value': (crc32(request.GET.get('status')),),
            })

        # Author filter
        if request.GET.get('author') is not None:
            filters_f.append({
                'filter': 'author',
                'value': (crc32(request.GET.get('author')),
                           crc32(request.GET.get('author') + ' (anon)'),),
            })

        # Created filter
        if request.GET.get('created') is not None:
            pass

        documents += fc.query(q, filters_f)

    results = []
    for i in range(offset, offset + 10):
        if documents[i]['attrs'].get('category', False):
            results.append(WikiPage.objects.get(pk=documents[i]['id']))
        else:
            results.append(ForumThread.objects.get(pk=documents[i]['id']))

    return jingo.render(request, 'search/results.html',
        {'num_results': len(documents), 'results': results, 'q': q,
          'locale': request.LANGUAGE_CODE, })
