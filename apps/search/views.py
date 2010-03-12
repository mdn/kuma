# Create your views here.

# required for building the query
# see refine_query variable
from flatqs import flatten
from django.utils.datastructures import MultiValueDict

from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse

import jingo

from sumo.utils import paginate
from sumo.models import ForumThread, WikiPage, Forum, Category

from .clients import ForumClient, WikiClient
from .utils import crc32

import search as CONSTANTS

# TODO: use lazy gettext, as in zamboni
from django.utils.translation import ugettext


def search(request):
    search_form = SearchForm(request.GET.copy())

    q = request.GET.get('q', '')
    refine_query = {'q': q}

    locale = request.GET.get('locale', request.LANGUAGE_CODE)
    sphinx_locale = (crc32(locale),)
    refine_query['locale'] = locale

    where = int(request.GET.get('w', CONSTANTS.WHERE_ALL))
    refine_query['w'] = where

    page = int(request.GET.get('page', 1))
    page = max(page, 1)
    offset = (page-1) * settings.SEARCH_RESULTS_PER_PAGE

    if (len(q) <= 0 or (request.GET.get('a', '0') == '1')):
        return jingo.render(request, 'form.html',
            {'locale': request.LANGUAGE_CODE,
            'advanced': request.GET.get('a', '0'),
            'request': request,
            'w': where, 'search_form': search_form,
            })

    documents = []

    if (where & CONSTANTS.WHERE_WIKI):
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

    if (where & CONSTANTS.WHERE_FORUM):
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
            """filters_f.append({
                'filter': 'status',
                'value': STATUS_LIST[request.GET.get('status')],
            })"""

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

    refine_query = MultiValueDict()
    for name, field in search_form.fields.items():
        refine_query[name] = request.GET.getlist(name)

    refine_query = 'a=1&' + flatten(refine_query, encode=False)
    refine_url = '%s?%s' % (reverse('search'), refine_query)

    return jingo.render(request, 'results.html',
        {'num_results': len(documents), 'results': results, 'q': q,
          'locale': request.LANGUAGE_CODE, 'pages': pages,
          'w': where, 'refine_url': refine_url,
          'search_form': search_form})


class SearchForm(forms.Form):
    q = forms.CharField()

    # kb form data
    tag = forms.CharField(label=ugettext('Tags'))

    language = forms.ChoiceField(label=ugettext('Language'),
        choices=settings.LANGUAGES)

    categories = []
    for cat in Category.objects.all():
        categories.append((cat.categId, cat.name))
    category = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label=ugettext('Category'), choices=categories)

    # forum form data
    status = forms.ChoiceField(label=ugettext('Post status'),
        choices=CONSTANTS.STATUS_LIST)
    author = forms.CharField()

    created = forms.ChoiceField(label=ugettext('Created'),
        choices=CONSTANTS.CREATED_LIST)
    created_date = forms.CharField()

    lastmodif = forms.ChoiceField(label=ugettext('Last updated'),
        choices=CONSTANTS.LUP_LIST)
    sortby = forms.ChoiceField(label=ugettext('Sort results by'),
        choices=CONSTANTS.SORTBY_LIST)

    forums = []
    for f in Forum.objects.all():
        forums.append((f.forumId, f.name))
    fid = forms.MultipleChoiceField(label=ugettext('Search in forum'),
        choices=forums)
