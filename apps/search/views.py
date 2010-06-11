import time
import re
import json
from datetime import datetime, timedelta

from django import forms
from django.forms.util import ValidationError
from django.conf import settings
from django.http import HttpResponse

import jingo
import jinja2
from tower import ugettext as _

from forums.models import Forum as DiscussionForum, Thread, Post
from sumo.models import ForumThread, WikiPage, Category
from sumo.utils import paginate, urlencode
from .clients import SupportClient, WikiClient, DiscussionClient, SearchError
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

            if ('a' not in cleaned_data or
                not cleaned_data['a']) and cleaned_data['q'] == '':
                raise ValidationError('Basic search requires a query string.')

            # Validate created and updated dates
            date_fields = (('created', 'created_date'),
                           ('updated', 'updated_date'))
            for field_option, field_date in date_fields:
                if cleaned_data[field_date] != '':
                    try:
                        created_timestamp = time.mktime(
                            time.strptime(cleaned_data[field_date],
                                          '%m/%d/%Y'))
                        cleaned_data[field_date] = int(created_timestamp)
                    except (ValueError, OverflowError):
                        cleaned_data[field_option] = None
                else:
                    cleaned_data[field_option] = None

            # Validate all integer fields

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
                cleaned_data['forum'] = map(int, cleaned_data.get('forum'))
            except ValueError:
                cleaned_data['forum'] = None

            try:
                cleaned_data['thread_type'] = map(
                    int, cleaned_data.get('thread_type'))
            except ValueError:
                cleaned_data['thread_type'] = None

            return cleaned_data

        class NoValidateMultipleChoiceField(forms.MultipleChoiceField):
            def valid_value(self, value):
                return True

        # Common fields
        q = forms.CharField(required=False)

        w = forms.TypedChoiceField(
            widget=forms.HiddenInput, required=False, coerce=int,
            empty_value=constants.WHERE_BASIC,
            choices=((constants.WHERE_SUPPORT, None),
                     (constants.WHERE_WIKI, None),
                     (constants.WHERE_BASIC, None),
                     (constants.WHERE_DISCUSSION, None)))

        a = forms.IntegerField(widget=forms.HiddenInput, required=False)

        # KB fields
        tag_widget = forms.TextInput(attrs={'placeholder':_('tag1, tag2')})
        tags = forms.CharField(label=_('Tags'), required=False,
                               widget=tag_widget)

        language = forms.ChoiceField(
            label=_('Language'), required=False,
            choices=[(LOCALES[k].external, LOCALES[k].native) for
                     k in settings.SUMO_LANGUAGES])

        categories = [(cat.categId, cat.name) for
                      cat in Category.objects.all()]
        category = NoValidateMultipleChoiceField(
            widget=forms.CheckboxSelectMultiple,
            label=_('Category'), choices=categories, required=False)

        # Support and discussion forums fields
        status = forms.TypedChoiceField(
            label=_('Post status'), coerce=int, empty_value=0,
            choices=constants.STATUS_LIST, required=False)

        author_widget = forms.TextInput(attrs={'placeholder':_('username')})
        author = forms.CharField(required=False, widget=author_widget)

        created = forms.TypedChoiceField(
            label=_('Created'), coerce=int, empty_value=0,
            choices=constants.DATE_LIST, required=False)
        created_date = forms.CharField(required=False)

        updated = forms.TypedChoiceField(
            label=_('Last updated'), coerce=int, empty_value=0,
            choices=constants.DATE_LIST, required=False)
        updated_date = forms.CharField(required=False)

        sortby = forms.TypedChoiceField(
            label=_('Sort results by'), coerce=int, empty_value=0,
            choices=constants.SORTBY_LIST, required=False)

        thread_type = NoValidateMultipleChoiceField(
            label=_('Thread type'), choices=constants.DISCUSSION_STATUS_LIST,
            required=False,
            widget=forms.CheckboxSelectMultiple)

        forums = [(f.id, f.name) for f in DiscussionForum.objects.all()]
        forum = NoValidateMultipleChoiceField(label=_('Search in forum'),
                                              choices=forums, required=False)

    # JSON-specific variables
    is_json = (request.GET.get('format') == 'json')
    callback = request.GET.get('callback', '').strip()
    mimetype = 'application/x-javascript' if callback else 'application/json'

    # Search "Expires" header format
    expires_fmt = '%A, %d %B %Y %H:%M:%S GMT'

    # Check callback is valid
    if is_json and callback and not jsonp_is_valid(callback):
        return HttpResponse(
            json.dumps({'error': _('Invalid callback function.')}),
            mimetype=mimetype, status=400)

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
        r['w'] = r.get('w', constants.WHERE_BASIC)
    # Advanced form
    if a == '2':
        r['language'] = language
        r['a'] = '1'

    search_form = SearchForm(r)

    if not search_form.is_valid() or a == '2':
        if is_json:
            return HttpResponse(
                json.dumps({'error': _('Invalid search data.')}),
                mimetype=mimetype,
                status=400)
        else:
            search_ = jingo.render(request, 'form.html',
                                {'advanced': a, 'request': request,
                                 'search_form': search_form})
            search_['Cache-Control'] = 'max-age=%s' % \
                                       (settings.SEARCH_CACHE_PERIOD * 60)
            search_['Expires'] = (datetime.utcnow() +
                                  timedelta(
                                    minutes=settings.SEARCH_CACHE_PERIOD)) \
                                  .strftime(expires_fmt)
            return search_

    cleaned = search_form.cleaned_data
    search_locale = (crc32(LOCALES[language].internal),)

    try:
        page = int(request.GET.get('page', 1))
        page = max(page, 1)
    except ValueError:
        page = 1
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
    # End of wiki filters

    # Support forum specific filters
    if cleaned['w'] & constants.WHERE_SUPPORT:
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

        if cleaned['author']:
            filters_f.append({
                'filter': 'author_ord',
                'value': (crc32(cleaned['author']),
                          crc32(cleaned['author'] +
                              ' (anon)'),),
            })

    # Discussion forum specific filters
    if cleaned['w'] & constants.WHERE_DISCUSSION:
        if cleaned['author']:
            filters_f.append({
                'filter': 'author_ord',
                'value': (crc32(cleaned['author']),),
            })

        if cleaned['thread_type']:
            if constants.DISCUSSION_STICKY in cleaned['thread_type']:
                filters_f.append({
                    'filter': 'is_sticky',
                    'value': (1,),
                })

            if constants.DISCUSSION_LOCKED in cleaned['thread_type']:
                filters_f.append({
                    'filter': 'is_locked',
                    'value': (1,),
                })

        if cleaned['forum']:
            filters_f.append({
                'filter': 'forum_id',
                'value': cleaned['forum'],
            })

    # Filters common to support and discussion forums
    # Created filter
    unix_now = int(time.time())
    date_filters = (('created', cleaned['created'], cleaned['created_date']),
                    ('updated', cleaned['updated'], cleaned['updated_date']))
    for filter_name, filter_option, filter_date in date_filters:
        if filter_option == constants.DATE_BEFORE:
            filters_f.append({
                'range': True,
                'filter': filter_name,
                'min': 0,
                'max': max(filter_date, 0),
            })
        elif filter_option == constants.DATE_AFTER:
            filters_f.append({
                'range': True,
                'filter': filter_name,
                'min': min(filter_date, unix_now),
                'max': unix_now,
            })

    sortby = int(request.GET.get('sortby', 0))
    try:
        if cleaned['w'] & constants.WHERE_WIKI:
            wc = WikiClient()  # Wiki SearchClient instance
            # Execute the query and append to documents
            documents += wc.query(cleaned['q'], filters_w)

        if cleaned['w'] & constants.WHERE_SUPPORT:
            sc = SupportClient()  # Support forum SearchClient instance

            # Sort results by
            try:
                sc.set_sort_mode(constants.SORT[sortby][0],
                                 constants.SORT[sortby][1])
            except IndexError:
                pass

            documents += sc.query(cleaned['q'], filters_f)

        if cleaned['w'] & constants.WHERE_DISCUSSION:
            dc = DiscussionClient()  # Discussion forums SearchClient instance

            # Sort results by
            try:
                dc.set_groupsort(constants.GROUPSORT[sortby])
            except IndexError:
                pass

            documents += dc.query(cleaned['q'], filters_f)

    except SearchError:
        if is_json:
            return HttpResponse(json.dumps({'error':
                                             _('Search Unavailable')}),
                                mimetype=mimetype, status=503)
        else:
            return jingo.render(request, 'down.html', {}, status=503)

    pages = paginate(request, documents, settings.SEARCH_RESULTS_PER_PAGE)

    results = []
    for i in range(offset, offset + settings.SEARCH_RESULTS_PER_PAGE):
        try:
            if documents[i]['attrs'].get('category', False) != False:
                wiki_page = WikiPage.objects.get(pk=documents[i]['id'])

                excerpt = wc.excerpt(wiki_page.data, cleaned['q'])
                summary = jinja2.Markup(excerpt)

                result = {'search_summary': summary,
                          'url': wiki_page.get_url(),
                          'title': wiki_page.name, }
                results.append(result)
            elif documents[i]['attrs'].get('forumid', False) != False:
                support_thread = ForumThread.objects.get(pk=documents[i]['id'])

                excerpt = sc.excerpt(support_thread.data, cleaned['q'])
                summary = jinja2.Markup(excerpt)

                result = {'search_summary': summary,
                          'url': support_thread.get_url(),
                          'title': support_thread.name, }
                results.append(result)
            else:
                thread = Thread.objects.get(
                    pk=documents[i]['attrs']['thread_id'])
                post = Post.objects.get(pk=documents[i]['id'])

                excerpt = dc.excerpt(post.content, cleaned['q'])
                summary = jinja2.Markup(excerpt)

                result = {'search_summary': summary,
                          'url': thread.get_absolute_url(),
                          'title': thread.title, }
                results.append(result)
        except IndexError:
            break
        except (WikiPage.DoesNotExist, ForumThread.DoesNotExist,
                Thread.DoesNotExist):
            continue

    items = [(k, v) for k in search_form.fields for
             v in r.getlist(k) if v and k != 'a']
    items.append(('a', '2'))

    refine_query = u'?%s' % urlencode(items)

    if is_json:
        data = {}
        data['results'] = results
        data['total'] = len(results)
        data['query'] = cleaned['q']
        if not results:
            data['message'] = _('No pages matched the search criteria')
        json_data = json.dumps(data)
        if callback:
            json_data = callback + '(' + json_data + ');'

        return HttpResponse(json_data, mimetype=mimetype)

    results_ = jingo.render(request, 'results.html',
        {'num_results': len(documents), 'results': results, 'q': cleaned['q'],
         'pages': pages, 'w': cleaned['w'], 'refine_query': refine_query,
         'search_form': search_form, 'lang_name': lang_name, })
    results_['Cache-Control'] = 'max-age=%s' % \
                                (settings.SEARCH_CACHE_PERIOD * 60)
    results_['Expires'] = (datetime.utcnow() +
                           timedelta(minutes=settings.SEARCH_CACHE_PERIOD)) \
                           .strftime(expires_fmt)
    return results_
