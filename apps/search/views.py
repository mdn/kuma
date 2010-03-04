# Create your views here.

from django.conf import settings

import jingo

from sumo.utils import paginate
from sumo.models import ForumThread, WikiPage

from .clients import ForumClient, WikiClient
from .utils import crc32

import urllib


WHERE_WIKI = 1
WHERE_FORUM = 2
WHERE_ALL = WHERE_WIKI | WHERE_FORUM

# Forum status constants
STATUS_STICKY = crc32('s')
STATUS_PROPOSED = crc32('p')
STATUS_REQUEST = crc32('r')
STATUS_NORMAL = crc32('n')
STATUS_ORIGINALREPLY = crc32('g')
STATUS_HOT = crc32('h')
STATUS_ANNOUNCE = crc32('a')
STATUS_INVALID = crc32('i')
STATUS_LOCKED = crc32('l')
STATUS_ARCHIVE = crc32('v')
STATUS_SOLVED = crc32('o')

STATUS_ALIAS_NO = 0
STATUS_ALIAS_NR = 91
STATUS_ALIAS_NH = 92
STATUS_ALIAS_HA = 93
STATUS_ALIAS_SO = 94
STATUS_ALIAS_AR = 95
STATUS_ALIAS_OT = 96

STATUS_LIST = {
    STATUS_ALIAS_NO: {
            'name': "Don't filter",
            },
    STATUS_ALIAS_NR: {
            'name': 'Has no replies',
            },
    STATUS_ALIAS_NH: {
            'name': 'Needs help',
            'value': (STATUS_NORMAL, STATUS_ORIGINALREPLY)
            },
    STATUS_ALIAS_HA: {
            'name': 'Has an answer',
            'value': (STATUS_PROPOSED, STATUS_REQUEST)
            },
    STATUS_ALIAS_SO: {
            'name': 'Solved',
            'value': (STATUS_SOLVED,)
            },
    STATUS_ALIAS_AR: {
            'name': 'Archived',
            'value': (STATUS_ARCHIVE,)
            },
    STATUS_ALIAS_OT: {
            'name': 'Other',
            'value': (STATUS_LOCKED, STATUS_STICKY, STATUS_ANNOUNCE, STATUS_INVALID, STATUS_HOT)
            },
}

SORTBY_RELEVANCE = 1
SORTBY_LASTMODIF = 2
SORTBY_CREATED = 3
SORTBY_REPLYCOUNT = 4

SORTBY_LIST = {
    SORTBY_RELEVANCE: "Relevance",
    SORTBY_LASTMODIF: "Last post date",
    SORTBY_CREATED: "Original post date",
    SORTBY_REPLYCOUNT: "Number of replies",
}

LASTMODIF_LIST = {
    0: "Don't filter",
    1: "Last 24 hours",
    7: "Last week",
    30: "Last month",
    180: "Last 6 months",
}

def search(request):
    q = request.GET.get('q', '')
    refine_query = {'q': q}

    if (len(q) <= 0 or (request.GET.get('a', '0') == '1')):
        return jingo.render(request, 'form.html',
            {'locale': request.LANGUAGE_CODE,
            'advanced': request.GET.get('a', '0'),
            'status_list': STATUS_LIST,
            'languages': settings.LANGUAGES,
            'lastmodif_list': LASTMODIF_LIST,
            'sortby_list': SORTBY_LIST,
            'tag': request.GET.get('tag', ''),
            'status': request.GET.get('status'),
            })

    locale = request.GET.get('locale', request.LANGUAGE_CODE)
    sphinx_locale = (crc32(locale),)
    refine_query['locale'] = locale

    where = int(request.GET.get('w', WHERE_ALL))
    refine_query['w'] = where

    page = int(request.GET.get('page', 1))
    page = max(page, 1)
    offset = (page-1)*settings.SEARCH_RESULTS_PER_PAGE

    documents = []

    if (where & WHERE_WIKI):
        wc = WikiClient() # Wiki SearchClient instance
        filters_w = [] # filters for the wiki search

        # Category filter

        categories = request.GET.get('category[]',
                        settings.SEARCH_DEFAULT_CATEGORIES)
        filters_w.append({
            'filter': 'category',
            'value': map(int,
                         categories.split(',')),
        })
        refine_query['category[]'] = categories
        #for category in categories:
         #   refine_query['category[]'].append(category)


        # Locale filter
        filters_w.append({
            'filter': 'locale',
            'value': sphinx_locale,
        })

        # Tag filter
        tag = request.GET.get('tag', '')
        if (tag is not None) and len(tag) > 0:
            filters_w.append({
                'filter': 'tag',
                'value': map(crc32, request.GET.get('tag').split(',')),
            })

        refine_query['tag'] = tag

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
                'value': STATUS_LIST[request.GET.get('status')],
            })

        refine_query['status'] = request.GET.get('status', '0')

        # Author filter
        if request.GET.get('author') is not None:
            filters_f.append({
                'filter': 'author',
                'value': (crc32(request.GET.get('author')),
                           crc32(request.GET.get('author') + ' (anon)'),),
            })

        refine_query['author'] = request.GET.get('author', '')

        # Created filter
        if request.GET.get('created') is not None:
            pass

        refine_query['created'] = request.GET.get('created', '')

        documents += fc.query(q, filters_f)

    pages = paginate(request, documents, settings.SEARCH_RESULTS_PER_PAGE)

    results = []
    for i in range(offset, offset + settings.SEARCH_RESULTS_PER_PAGE):
        try:
            if documents[i]['attrs'].get('category', False):
                wiki_page = WikiPage.objects.get(pk=documents[i]['id'])
                result = {'search_summary': wc.excerpt(wiki_page.data, q),
                    'url': wiki_page.get_url(),
                    'title': wiki_page.name,
                    }
                results.append(result)
            else:
                forum_thread = ForumThread.objects.get(pk=documents[i]['id'])
                result = {'search_summary': fc.excerpt(forum_thread.data, q),
                    'url': forum_thread.get_url(),
                    'title': forum_thread.name,
                    }
                results.append(result)
        except IndexError:
            break
        except (WikiPage.DoesNotExist, ForumThread.DoesNotExist):
            continue

    refine_query = '?a=1&' + '&'.join([k+'='+urllib.quote(str(v)) for (k,v) in refine_query.items()])
    return jingo.render(request, 'results.html',
        {'num_results': len(documents), 'results': results, 'q': q,
          'locale': request.LANGUAGE_CODE, 'pages': pages,
          'w': where, 'refine_query': refine_query})
