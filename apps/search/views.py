import time
import re
import json

from django import forms
from django.forms.util import ValidationError
from django.conf import settings
from django.http import HttpResponse

import jingo
import jinja2
from tower import ugettext as _

from sumo.utils import paginate, urlencode
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

    # Form must be nested inside request for fixtures to be used properly
    class SearchForm(forms.Form):
        """Django form for handling display and validation"""

        def clean(self):
            """Clean up data and set defaults"""

            cleaned_data = self.cleaned_data

            if not cleaned_data['a'] and cleaned_data['q'] == '':
                raise ValidationError('Basic search requires a query string.')

            # Validate created date
            if cleaned_data['created_date'] != '':
                try:
                    cleaned_data['created_date'] = int(time.mktime(
                        time.strptime(cleaned_data['created_date'],
                            '%m/%d/%Y'), ))
                except ValueError:
                    raise ValidationError('Invalid created date.')

            # Set defaults for MultipleChoiceFields and convert to ints.
            # Ticket #12398 adds TypedMultipleChoiceField which would replace
            # MultipleChoiceField + map(int, ...) and use coerce instead.
            if cleaned_data.get('category'):
                try:
                    cleaned_data['category'] = map(int,
                                                   cleaned_data['category'])
                except ValueError:
                    cleaned_data['category'] = None
            try:
                cleaned_data['forum'] = map(int, cleaned_data.get('forum',
                                            settings.SEARCH_DEFAULT_FORUMS))
            except ValueError:
                cleaned_data['forum'] = None

            return cleaned_data

        # Common fields
        q = forms.CharField(required=False)

        w = forms.TypedChoiceField(widget=forms.HiddenInput,
                              required=False,
                              coerce=int,
                              empty_value=constants.WHERE_ALL,
                              choices=((constants.WHERE_FORUM, None),
                                       (constants.WHERE_WIKI, None),
                                       (constants.WHERE_ALL, None)))

        a = forms.IntegerField(widget=forms.HiddenInput, required=False)

        # KB fields
        tags = forms.CharField(label=_('Tags'), required=False)

        language = forms.ChoiceField(label=_('Language'), required=False,
            choices=[(LOCALES[k].external, LOCALES[k].native) for
                     k in settings.SUMO_LANGUAGES])

        categories = [(cat.categId, cat.name) for
                      cat in Category.objects.all()]
        category = forms.MultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            label=_('Category'), choices=categories, required=False)

        # Forum fields
        status = forms.TypedChoiceField(label=_('Post status'), coerce=int,
            choices=constants.STATUS_LIST, empty_value=0, required=False)
        author = forms.CharField(required=False)

        created = forms.TypedChoiceField(label=_('Created'), coerce=int,
            choices=constants.CREATED_LIST, empty_value=0, required=False)
        created_date = forms.CharField(required=False)

        lastmodif = forms.TypedChoiceField(label=_('Last updated'), coerce=int,
            choices=constants.LUP_LIST, empty_value=0, required=False)
        sortby = forms.TypedChoiceField(label=_('Sort results by'), coerce=int,
            choices=constants.SORTBY_LIST, empty_value=0, required=False)

        forums = [(f.forumId, f.name) for f in Forum.objects.all()]
        forum = forms.MultipleChoiceField(label=_('Search in forum'),
            choices=forums, required=False)

    language = request.GET.get('language', request.locale)
    if not language in LOCALES:
        language = settings.LANGUAGE_CODE
    r = request.GET.copy()
    a = request.GET.get('a', '0')

    # Search default values
    try:
        category = map(int, r.getlist('category')) or \
                  settings.SEARCH_DEFAULT_CATEGORIES
    except ValueError:
        category = settings.SEARCH_DEFAULT_CATEGORIES
    r.setlist('category', [x for x in category if x > 0])
    exclude_category = [abs(x) for x in category if x < 0]
    # Basic form
    if a == '0':
        r['w'] = r.get('w', constants.WHERE_ALL)
        r.setlist('forum', settings.SEARCH_DEFAULT_FORUMS)
    # Advanced form
    if a == '2':
        r.setlist('forum', settings.SEARCH_DEFAULT_FORUMS)
        r['language'] = language
        r['a'] = '1'

    search_form = SearchForm(r)

    if not search_form.is_valid() or a == '2':
        return jingo.render(request, 'form.html',
                            {'advanced': a, 'request': request,
                             'search_form': search_form})

    cleaned = search_form.cleaned_data
    search_locale = (crc32(LOCALES[language].internal),)
    page = int(request.GET.get('page', 1))
    page = max(page, 1)
    offset = (page - 1) * settings.SEARCH_RESULTS_PER_PAGE

    # get language name for display in template
    lang = language.lower()
    if settings.LANGUAGES.get(lang):
        lang_name = settings.LANGUAGES[lang]
    else:
        lang_name = ''

    documents = []
    filters_w = []
    filters_f = []

    # wiki filters
    # Category filter
    if cleaned['category']:
        filters_w.append({
            'filter': 'category',
            'value': cleaned['category'],
        })

    if exclude_category:
        filters_w.append({
            'filter': 'category',
            'value': exclude_category,
            'exclude': True,
        })

    # Locale filter
    filters_w.append({
        'filter': 'locale',
        'value': search_locale,
    })

    # Tags filter
    tags = [crc32(t.strip()) for t in cleaned['tags'].split()]
    if tags:
        for t in tags:
            filters_w.append({
                'filter': 'tag',
                'value': (t,),
                })

    # Forum filter
    if cleaned['forum']:
        filters_f.append({
            'filter': 'forumId',
            'value': cleaned['forum'],
        })

    # Status filter
    status = cleaned['status']
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
    if cleaned['author']:
        filters_f.append({
            'filter': 'author_ord',
            'value': (crc32(cleaned['author']),
                      crc32(cleaned['author'] +
                          ' (anon)'),),
        })

    # Created filter
    unix_now = int(time.time())
    if cleaned['created'] == constants.CREATED_BEFORE:
        filters_f.append({
            'range': True,
            'filter': 'created',
            'min': 0,
            'max': cleaned['created_date'],
        })
    elif cleaned['created'] == constants.CREATED_AFTER:
        filters_f.append({
            'range': True,
            'filter': 'created',
            'min': cleaned['created_date'],
            'max': unix_now,
        })

    # Last modified filter
    if cleaned['lastmodif']:
        filters_f.append({
            'range': True,
            'filter': 'last_updated',
            'min': unix_now - constants.LUP_MULTIPLIER *
                cleaned['lastmodif'],
            'max': unix_now,
        })

    try:
        if (cleaned['w'] & constants.WHERE_WIKI):
            wc = WikiClient()  # Wiki SearchClient instance
            # Execute the query and append to documents
            documents += wc.query(cleaned['q'], filters_w)

        if (cleaned['w'] & constants.WHERE_FORUM):
            fc = ForumClient()  # Forum SearchClient instance

            # Sort results by
            sortby = int(request.GET.get('sortby', 0))
            try:
                fc.set_sort_mode(constants.SORT[sortby][0],
                                 constants.SORT[sortby][1])
            except IndexError:
                pass

            documents += fc.query(cleaned['q'], filters_f)
    except SearchError:
        return jingo.render(request, 'down.html', {}, status=503)

    pages = paginate(request, documents, settings.SEARCH_RESULTS_PER_PAGE)

    results = []
    for i in range(offset, offset + settings.SEARCH_RESULTS_PER_PAGE):
        try:
            if documents[i]['attrs'].get('category', False):
                wiki_page = WikiPage.objects.get(pk=documents[i]['id'])

                excerpt = wc.excerpt(wiki_page.data, cleaned['q'])
                summary = jinja2.Markup(excerpt)

                result = {'search_summary': summary,
                          'url': wiki_page.get_url(),
                          'title': wiki_page.name, }
                results.append(result)
            else:
                forum_thread = ForumThread.objects.get(pk=documents[i]['id'])

                excerpt = fc.excerpt(forum_thread.data, cleaned['q'])
                summary = jinja2.Markup(excerpt)

                result = {'search_summary': summary,
                          'url': forum_thread.get_url(),
                          'title': forum_thread.name, }
                results.append(result)
        except IndexError:
            break
        except (WikiPage.DoesNotExist, ForumThread.DoesNotExist):
            continue

    items = [(k, v) for k in search_form.fields
             for v in r.getlist(k)
                if v and k != 'a']
    items.append(('a', '2'))

    refine_query = u'?%s' % urlencode(items)

    if request.GET.get('format') == 'json':
        callback = request.GET.get('callback', '').strip()
        # Check callback is valid
        if callback and not jsonp_is_valid(callback):
                return HttpResponse('', mimetype='application/x-javascript',
                    status=400)

        data = {}
        data['results'] = results
        data['total'] = len(documents)
        data['query'] = cleaned['q']
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
        {'num_results': len(documents), 'results': results, 'q': cleaned['q'],
         'pages': pages, 'w': cleaned['w'], 'refine_query': refine_query,
         'search_form': search_form, 'lang_name': lang_name, })
