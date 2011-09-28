import time
import re
import json
from datetime import datetime, timedelta

from django.conf import settings
from django.contrib.sites.models import Site
from django.db.models import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseBadRequest
from django.utils.http import urlencode
from django.views.decorators.cache import cache_page

import jingo
import jinja2
from tower import ugettext as _

from search.clients import (QuestionsClient, WikiClient,
                            DiscussionClient, SearchError)
from search.utils import crc32, locale_or_default, sphinx_locale
from forums.models import Thread, Post
from questions.models import Question
import search as constants
from search.forms import SearchForm
from sumo.utils import paginate, smart_int
from wiki.models import Document, FIREFOX_VERSIONS, OPERATING_SYSTEMS


def jsonp_is_valid(func):
    func_regex = re.compile(r'^[a-zA-Z_\$][a-zA-Z0-9_\$]*'
        + r'(\[[a-zA-Z0-9_\$]*\])*(\.[a-zA-Z0-9_\$]+(\[[a-zA-Z0-9_\$]*\])*)*$')
    return func_regex.match(func)


def search(request):
    """Performs search or displays the search form."""

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

    language = locale_or_default(request.GET.get('language', request.locale))
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

    try:
        fx = map(int, r.getlist('fx')) or [v.id for v in FIREFOX_VERSIONS]
    except ValueError:
        fx = [v.id for v in FIREFOX_VERSIONS]
    #r.setlist('fx', fx)

    try:
        os = map(int, r.getlist('os')) or [o.id for o in OPERATING_SYSTEMS]
    except ValueError:
        os = [o.id for o in OPERATING_SYSTEMS]
    #r.setlist('os', os)

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

        search_ = jingo.render(request, 'search/form.html',
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
    search_locale = (sphinx_locale(language),)

    page = max(smart_int(request.GET.get('page')), 1)
    offset = (page - 1) * settings.SEARCH_RESULTS_PER_PAGE

    # get language name for display in template
    lang = language.lower()
    if settings.LANGUAGES.get(lang):
        lang_name = settings.LANGUAGES[lang]
    else:
        lang_name = ''

    documents = []
    filters_w = []
    filters_q = []
    filters_f = []

    # wiki filters
    # Version and OS filters
    if cleaned['fx']:
        filters_w.append({
            'filter': 'fx',
            'value': cleaned['fx'],
        })

    if cleaned['os']:
        filters_w.append({
            'filter': 'os',
            'value': cleaned['os'],
        })

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

    """
    # Support questions specific filters
    if cleaned['w'] & constants.WHERE_SUPPORT:

        # Solved is set by default if using basic search
        if a == '0' and not cleaned['is_solved']:
            cleaned['is_solved'] = constants.TERNARY_YES

        # These filters are ternary, they can be either YES, NO, or OFF
        toggle_filters = ('is_locked', 'is_solved', 'has_answers',
                          'has_helpful')
        for filter_name in toggle_filters:
            if cleaned[filter_name] == constants.TERNARY_YES:
                filters_q.append({
                    'filter': filter_name,
                    'value': (True,),
                })
            if cleaned[filter_name] == constants.TERNARY_NO:
                filters_q.append({
                    'filter': filter_name,
                    'value': (False,),
                })

        if cleaned['asked_by']:
            filters_q.append({
                'filter': 'question_creator',
                'value': (crc32(cleaned['asked_by']),),
            })

        if cleaned['answered_by']:
            filters_q.append({
                'filter': 'answer_creator',
                'value': (crc32(cleaned['answered_by']),),
            })

        q_tags = [crc32(t.strip()) for t in cleaned['q_tags'].split()]
        if q_tags:
            for t in q_tags:
                filters_q.append({
                    'filter': 'tag',
                    'value': (t,),
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
    """
    # Filters common to support and discussion forums
    # Created filter
    unix_now = int(time.time())
    interval_filters = (
#        ('created', cleaned['created'], cleaned['created_date']),
        ('updated', cleaned['updated'], cleaned['updated_date']),
#        ('question_votes', cleaned['num_voted'], cleaned['num_votes'])
    )
    for filter_name, filter_option, filter_date in interval_filters:
        if filter_option == constants.INTERVAL_BEFORE:
            before = {
                'range': True,
                'filter': filter_name,
                'min': 0,
                'max': max(filter_date, 0),
            }
            if filter_name != 'question_votes':
                filters_f.append(before)
            filters_q.append(before)
        elif filter_option == constants.INTERVAL_AFTER:
            after = {
                'range': True,
                'filter': filter_name,
                'min': min(filter_date, unix_now),
                'max': unix_now,
            }
            if filter_name != 'question_votes':
                filters_f.append(after)
            filters_q.append(after)

    sortby = smart_int(request.GET.get('sortby'))
    try:
        if cleaned['w'] & constants.WHERE_WIKI:
            wc = WikiClient()  # Wiki SearchClient instance
            # Execute the query and append to documents
            documents += wc.query(cleaned['q'], filters_w)

        if cleaned['w'] & constants.WHERE_SUPPORT:
            qc = QuestionsClient()  # Support question SearchClient instance

            # Sort results by
            try:
                qc.set_sort_mode(constants.SORT_QUESTIONS[sortby][0],
                                 constants.SORT_QUESTIONS[sortby][1])
            except IndexError:
                pass

            documents += qc.query(cleaned['q'], filters_q)

        if cleaned['w'] & constants.WHERE_DISCUSSION:
            dc = DiscussionClient()  # Discussion forums SearchClient instance

            # Sort results by
            try:
                dc.groupsort = constants.GROUPSORT[sortby]
            except IndexError:
                pass

            documents += dc.query(cleaned['q'], filters_f)

    except SearchError:
        if is_json:
            return HttpResponse(json.dumps({'error':
                                             _('Search Unavailable')}),
                                mimetype=mimetype, status=503)

        return jingo.render(request, 'search/down.html', {}, status=503)

    pages = paginate(request, documents, settings.SEARCH_RESULTS_PER_PAGE)

    results = []
    for i in range(offset, offset + settings.SEARCH_RESULTS_PER_PAGE):
        try:
            if documents[i]['attrs'].get('category', False) != False:
                wiki_page = Document.objects.get(pk=documents[i]['id'])
                summary = wiki_page.current_revision.summary

                result = {'search_summary': summary,
                          'url': wiki_page.get_absolute_url(),
                          'title': wiki_page.title,
                          'type': 'document', }
                results.append(result)
            elif documents[i]['attrs'].get('question_creator', False) != False:
                question = Question.objects.get(
                    pk=documents[i]['attrs']['question_id'])

                excerpt = qc.excerpt(question.content, cleaned['q'])
                summary = jinja2.Markup(excerpt)

                result = {'search_summary': summary,
                          'url': question.get_absolute_url(),
                          'title': question.title,
                          'type': 'question', }
                results.append(result)
            else:
                thread = Thread.objects.get(
                    pk=documents[i]['attrs']['thread_id'])
                post = Post.objects.get(pk=documents[i]['id'])

                excerpt = dc.excerpt(post.content, cleaned['q'])
                summary = jinja2.Markup(excerpt)

                result = {'search_summary': summary,
                          'url': thread.get_absolute_url(),
                          'title': thread.title,
                          'type': 'thread', }
                results.append(result)
        except IndexError:
            break
        except ObjectDoesNotExist:
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

    results_ = jingo.render(request, 'search/results.html',
        {'num_results': len(documents), 'results': results, 'q': cleaned['q'],
         'pages': pages, 'w': cleaned['w'], 'refine_query': refine_query,
         'search_form': search_form, 'lang_name': lang_name, })
    results_['Cache-Control'] = 'max-age=%s' % \
                                (settings.SEARCH_CACHE_PERIOD * 60)
    results_['Expires'] = (datetime.utcnow() +
                           timedelta(minutes=settings.SEARCH_CACHE_PERIOD)) \
                           .strftime(expires_fmt)
    return results_


@cache_page(60 * 15)  # 15 minutes.
def suggestions(request):
    """A simple search view that returns OpenSearch suggestions."""

    mimetype = 'application/x-suggestions+json'

    term = request.GET.get('q')

    if not term:
        return HttpResponseBadRequest(mimetype=mimetype)

    wc = WikiClient()
    qc = QuestionsClient()
    site = Site.objects.get_current()
    locale = sphinx_locale(locale_or_default(request.locale))

    results = []
    filters_w = [{'filter': 'locale', 'value': (locale,)}]
    filters_q = [{'filter': 'has_helpful', 'value': (True,)}]

    for client, filter, cls in [(wc, filters_w, Document),
                                (qc, filters_q, Question)]:
        for result in client.query(term, filter, limit=5):
            try:
                result = cls.objects.get(pk=result['id'])
            except cls.DoesNotExist:
                continue
            results.append(result)

    urlize = lambda obj: u'https://%s%s' % (site, obj.get_absolute_url())
    data = [term, [r.title for r in results], [], [urlize(r) for r in results]]
    return HttpResponse(json.dumps(data), mimetype=mimetype)


@cache_page(60 * 60 * 168)  # 1 week.
def plugin(request):
    """Render an OpenSearch Plugin."""
    site = Site.objects.get_current()
    return jingo.render(request, 'search/plugin.html',
                        {'site': site, 'locale': request.locale},
                        mimetype='application/opensearchdescription+xml')
