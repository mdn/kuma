# Create your views here.

import time
import re
import json

from django.utils.datastructures import MultiValueDict
from django import forms
from django.conf import settings
from django.http import HttpResponse

import jingo
from tower import ugettext as _
from flatqs import flatten

from sumo.utils import paginate
from sumo.models import ForumThread, WikiPage, Forum, Category
from .clients import ForumClient, WikiClient, SearchError
from .utils import crc32
import search as constants
from sumo_locales import LOCALES


def jsonp_is_valid(func):
    func_regex = re.compile(r'^[a-zA-Z_\$][a-zA-Z0-9_\$]*'
        + r'(\[[a-zA-Z0-9_\$]*\])*(\.[a-zA-Z0-9_\$]+(\[[a-zA-Z0-9_\$]*\])*)*$')
    return func_regex.match(func)


def search(request):
    """Performs search or displays the search form"""

    # set up query variables
    q = request.GET.get('q', '')

    language = request.GET.get('language', request.locale)
    if language in LOCALES:
        language = LOCALES[language].internal
    else:
        language = LOCALES[settings.LANGUAGE_CODE].internal

    search_locale = (crc32(language),)

    where = int(request.GET.get('w', constants.WHERE_ALL))

    page = int(request.GET.get('page', 1))
    page = max(page, 1)
    offset = (page - 1) * settings.SEARCH_RESULTS_PER_PAGE

    # set up form with default values
    search_params = request.GET.copy()
    if not search_params.getlist('category'):
        search_params.setlist('category', settings.SEARCH_DEFAULT_CATEGORIES)
    if not search_params.getlist('forum'):
        search_params.setlist('forum', settings.SEARCH_DEFAULT_FORUMS)
    if not search_params.getlist('language'):
        search_params.setlist('language', [language])
    search_form = SearchForm(search_params)

    # no query or advanced search?
    # => return empty form
    if (not q or (request.GET.get('a', '0') == '1')):
        return jingo.render(request, 'form.html',
            {'advanced': request.GET.get('a'), 'request': request,
            'w': where, 'search_form': search_form})

    # get language name for display in template
    lang = language.lower()
    if settings.LANGUAGES.get(lang):
        lang_name = settings.LANGUAGES[lang]
    else:
        lang_name = ''

    documents = []

    try:
        if (where & constants.WHERE_WIKI):
            wc = WikiClient()  # Wiki SearchClient instance
            filters_w = []  # Filters for the wiki search

            # Category filter
            categories = map(int, search_params.getlist('category'))
            filters_w.append({
                'filter': 'category',
                'value': [x for x in categories if x > 0],
            })

            exclude_categories = [abs(x) for x in categories if x < 0]
            if exclude_categories:
                filters_w.append({
                    'filter': 'category',
                    'value': exclude_categories,
                    'exclude': True,
                })

            # Locale filter
            filters_w.append({
                'filter': 'locale',
                'value': search_locale,
            })

            # Tag filter
            tag = [t.strip() for t in request.GET.get('tag', '').split()]
            if tag:
                tag = map(crc32, tag)
                for t in tag:
                    filters_w.append({
                        'filter': 'tag',
                        'value': (t,),
                    })

            # Execute the query and append to documents
            documents += wc.query(q, filters_w)

        if (where & constants.WHERE_FORUM):
            fc = ForumClient()  # Forum SearchClient instance
            filters_f = []  # Filters for the forum search

            # Forum filter
            filters_f.append({
                'filter': 'forumId',
                'value': map(int, search_params.getlist('forum')),
            })

            # Status filter
            status = int(request.GET.get('status', 0))
            # No replies case is not stored in status
            if status == constants.STATUS_ALIAS_NR:
                filters_f.append({
                    'filter': 'replies',
                    'value': (0,),
                })

                # Avoid filtering by status
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
                # No date => no filtering
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
                fc.set_sort_mode(constants.SORTBY_MODE, 'created')
            elif sortby == constants.SORTBY_LASTMODIF:
                fc.set_sort_mode(constants.SORTBY_MODE, 'last_updated')
            elif sortby == constants.SORTBY_REPLYCOUNT:
                fc.set_sort_mode(constants.SORTBY_MODE, 'replies')

            documents += fc.query(q, filters_f)
    except SearchError:
        return jingo.render(request, 'down.html', {}, status=503)

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

    refine_query = '?a=1&w=' + str(where) + '&' \
        + flatten(refine_query, encode=False)

    if request.GET.get('format') == 'json':
        callback = request.GET.get('callback', '').strip()
        # Check callback is valid
        if callback and not jsonp_is_valid(callback):
                return HttpResponse('', mimetype='application/x-javascript',
                    status=400)

        data = {}
        data['results'] = results
        data['total'] = len(documents)
        data['query'] = q
        if not results:
            data['message'] = _('No pages matched the search criteria')
        json_data = json.dumps(data)
        if callback:
            json_data = callback + '(' + json_data + ');'
            response = HttpResponse(json_data,
                mimetype='application/x-javascript')
        else:
            response = HttpResponse(json_data,
                mimetype='application/json')

        return response

    return jingo.render(request, 'results.html',
        {'num_results': len(documents), 'results': results, 'q': q,
          'pages': pages, 'w': where, 'refine_query': refine_query,
          'search_form': search_form, 'lang_name': lang_name, })


class SearchForm(forms.Form):
    q = forms.CharField()

    # KB form data
    tag = forms.CharField(label=_('Tags'))

    language = forms.ChoiceField(label=_('Language'),
        choices=[(i, settings.LANGUAGES[i]) for i in settings.LANGUAGES])

    categories = []
    for cat in Category.objects.all():
        categories.append((cat.categId, cat.name))
    category = forms.MultipleChoiceField(
        widget=forms.CheckboxSelectMultiple,
        label=_('Category'), choices=categories)

    # Forum form data
    status = forms.ChoiceField(label=_('Post status'),
        choices=constants.STATUS_LIST)
    author = forms.CharField()

    created = forms.ChoiceField(label=_('Created'),
        choices=constants.CREATED_LIST)
    created_date = forms.CharField()

    lastmodif = forms.ChoiceField(label=_('Last updated'),
        choices=constants.LUP_LIST)
    sortby = forms.ChoiceField(label=_('Sort results by'),
        choices=constants.SORTBY_LIST)

    forums = []
    for f in Forum.objects.all():
        forums.append((f.forumId, f.name))
    forum = forms.MultipleChoiceField(label=_('Search in forum'),
        choices=forums)
