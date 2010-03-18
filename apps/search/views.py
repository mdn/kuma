# Create your views here.

import time

from django.utils.datastructures import MultiValueDict
from django import forms
from django.conf import settings
from django.core.urlresolvers import reverse

import jingo
from l10n import ugettext
# required for building the query
# see refine_query variable
from flatqs import flatten

from sumo.utils import paginate
from sumo.models import ForumThread, WikiPage, Forum, Category
from .clients import ForumClient, WikiClient
from .utils import crc32
import search as constants


def search(request):
    """Performs search or displays the search form"""

    # set up form
    search_url = reverse('search')
    search_form = SearchForm(request.GET.copy())

    # set up query variables
    q = request.GET.get('q', '')

    locale = request.GET.get('locale', request.LANGUAGE_CODE)
    language = request.GET.get('language', locale)

    sphinx_locale = (crc32(language),)

    where = int(request.GET.get('w', constants.WHERE_ALL))

    page = int(request.GET.get('page', 1))
    page = max(page, 1)
    offset = (page-1) * settings.SEARCH_RESULTS_PER_PAGE

    # no query or advanced search?
    # => return empty form
    if (not q or (request.GET.get('a', '0') == '1')):
        return jingo.render(request, 'form.html',
            {'locale': request.LANGUAGE_CODE,
            'advanced': request.GET.get('a'),
            'request': request,
            'w': where, 'search_form': search_form,
            'search_url': search_url,
            })

    # get language name for display in template
    for (l, l_name) in settings.LANGUAGES:
        if l == language:
            lang_name = l_name

    documents = []

    if (where & constants.WHERE_WIKI):
        wc = WikiClient() # Wiki SearchClient instance
        filters_w = [] # filters for the wiki search


        # Category filter
        categories = request.GET.getlist('category') or \
            settings.SEARCH_DEFAULT_CATEGORIES
        filters_w.append({
            'filter': 'category',
            'value': map(int, categories),
        })


        # Locale filter
        filters_w.append({
            'filter': 'locale',
            'value': sphinx_locale,
        })


        # Tag filter
        tag = [t.strip() for t in request.GET.get('tag', '').split(',')]
        if tag:
            tag = map(crc32, tag)
            for t in tag:
                filters_w.append({
                    'filter': 'tag',
                    'value': (t,),
                })


        # execute the query and append to documents
        documents += wc.query(q, filters_w)

    if (where & constants.WHERE_FORUM):
        fc = ForumClient() # Forum SearchClient instance
        filters_f = [] # filters for the forum search

        # Forum filter
        filters_f.append({
            'filter': 'forumId',
            'value': map(int,
                request.GET.getlist('fid') or \
                    settings.SEARCH_DEFAULT_FORUMS),
        })

        # Status filter
        status = int(request.GET.get('status', 0))
        # no replies case is not stored in status
        if status == constants.STATUS_ALIAS_NR:
            filters_f.append({
                'filter': 'replies',
                'value': (0,),
            })

            # avoid filtering by status
            status = None

        if status:
            filters_f.append({
                'filter': 'status',
                'value': constants.STATUS_ALIAS_REVERSE[status],
            })

        # Author filter
        if request.GET.get('author'):
            filters_f.append({
                'filter': 'author_ord',
                'value': (crc32(request.GET.get('author')),
                           crc32(request.GET.get('author') + ' (anon)'),),
            })

        unix_now = int(time.time())
        # Created filter
        created = int(request.GET.get('created', 0))
        created_date = request.GET.get('created_date', '')

        if not created_date:
            # no date => no filtering
            created = None
        else:
            try:
                created_date = int(time.mktime(
                    time.strptime(created_date, '%m/%d/%Y'),
                    ))
            except ValueError:
                created = None


        if created == constants.CREATED_BEFORE:
            filters_f.append({
                'range': True,
                'filter': 'created',
                'min': 0,
                'max': created_date,
            })

        elif created == constants.CREATED_AFTER:
            filters_f.append({
                'range': True,
                'filter': 'created',
                'min': created_date,
                'max': int(unix_now),
            })


        # Last modified filter
        lastmodif = int(request.GET.get('lastmodif', 0))

        if lastmodif:
            filters_f.append({
                'range': True,
                'filter': 'last_updated',
                'min': unix_now - constants.LUP_MULTIPLIER * lastmodif,
                'max': unix_now,
            })

        # Sort results by
        sortby = int(request.GET.get('sortby', 0))
        if sortby == constants.SORTBY_CREATED:
            fc.sort(constants.SORTBY_MODE, 'created')
        elif sortby == constants.SORTBY_LASTMODIF:
            fc.sort(constants.SORTBY_MODE, 'last_updated')
        elif sortby == constants.SORTBY_REPLYCOUNT:
            fc.sort(constants.SORTBY_MODE, 'replies')

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

    refine_query = 'a=1&w=' + str(where) + '&' \
        + flatten(refine_query, encode=False)
    refine_url = '%s?%s' % (search_url, refine_query)

    return jingo.render(request, 'results.html',
        {'num_results': len(documents), 'results': results, 'q': q,
          'locale': request.LANGUAGE_CODE, 'pages': pages,
          'w': where, 'refine_url': refine_url,
          'search_form': search_form, 'search_url': search_url,
          'lang_name': lang_name, })


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
        choices=constants.STATUS_LIST)
    author = forms.CharField()

    created = forms.ChoiceField(label=ugettext('Created'),
        choices=constants.CREATED_LIST)
    created_date = forms.CharField()

    lastmodif = forms.ChoiceField(label=ugettext('Last updated'),
        choices=constants.LUP_LIST)
    sortby = forms.ChoiceField(label=ugettext('Sort results by'),
        choices=constants.SORTBY_LIST)

    forums = []
    for f in Forum.objects.all():
        forums.append((f.forumId, f.name))
    fid = forms.MultipleChoiceField(label=ugettext('Search in forum'),
        choices=forums)
