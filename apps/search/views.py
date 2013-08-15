import re
import json

from django.contrib.sites.models import Site
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import render
from django.views.decorators.cache import cache_page

from waffle import flag_is_active

from urlobject import URLObject

from wiki.models import DocumentType

from .forms import SearchForm


def jsonp_is_valid(func):
    func_regex = re.compile(r'^[a-zA-Z_\$][a-zA-Z0-9_\$]*'
        + r'(\[[a-zA-Z0-9_\$]*\])*(\.[a-zA-Z0-9_\$]+(\[[a-zA-Z0-9_\$]*\])*)*$')
    return func_regex.match(func)


def pop_param(url, name, value):
    """
    Takes an URLObject instance and removes the parameter with the given
    name and value -- if it exists.
    """
    param_dict = {}
    for param_name, param_values in url.query.multi_dict.items():
        if param_name == name:
            for param_value in param_values:
                if param_value != value:
                    param_dict.setdefault(param_name, []).append(param_value)
        else:
            param_dict[param_name] = param_values
    return url.del_query_param(name).set_query_params(param_dict)


def merge_param(url, name, value):
    """
    Takes an URLObject instance and adds a query parameter with the
    given name and value -- but prevents duplication.
    """
    param_dict = url.query.multi_dict
    if name in param_dict:
        for param_name, param_values in param_dict.items():
            if param_name == name:
                if value not in param_values:
                    param_values.append(value)
            param_dict[param_name] = param_values
    else:
        param_dict[name] = value
    return url.set_query_params(param_dict)


def search(request, page_count=10):
    """Performs search or displays the search form."""

    # Google Custom Search results page
    if not flag_is_active(request, 'elasticsearch'):
        query = request.GET.get('q', '')
        return render(request, 'landing/searchresults.html', {'query': query})

    search_form = SearchForm(request.GET or None)

    context = {
        'search_form': search_form,
    }

    if search_form.is_valid():
        search_query = search_form.cleaned_data.get('q', None)

        or_dict = {}
        for field in ['title', 'content', 'summary']:
            or_dict[field + '__text'] = search_query

        results = (DocumentType.search()
                               .query(or_=or_dict)
                               .filter(locale=request.locale)
                               .highlight(*DocumentType.excerpt_fields)
                               .facet('tags'))

        filtered_topics = search_form.cleaned_data.get('topic', [])

        if filtered_topics:
            results = results.filter(tags=filtered_topics)

        result_count = results.count()

        url = URLObject(request.get_full_path())

        # {u'tags': [{u'count': 1, u'term': u'html'}]}
        # then we go through the returned facets and match the items with
        # the allowed filters
        facet_counts = []
        topic_choices = search_form.topic_choices()
        for result_facet in results.facet_counts().get('tags', []):
            allowed_filter = topic_choices.get(result_facet['term'], None)
            if allowed_filter is None:
                continue

            facet_updates = {
                'label': allowed_filter,
                'select_url': merge_param(url, 'topic', result_facet['term']),
            }
            if result_facet['term'] in url.query.multi_dict.get('topic', []):
                result_facet['deselect_url'] = pop_param(url, 'topic',
                                                         result_facet['term'])

            facet_counts.append(dict(result_facet, **facet_updates))

        # Pagination
        current_page = search_form.cleaned_data['page']
        start = page_count * (current_page - 1)
        end = start + page_count
        results = results[start:end]

        context.update({
            'results': results,
            'search_query': search_query,
            'result_count': result_count,
            'facet_counts': facet_counts,
            'current_page': current_page,
            'prev_page': current_page - 1 if start > 0 else None,
            'next_page': current_page + 1 if end < result_count else None,
        })

    else:
        search_query = ''
        result_count = 0

    template = 'results.html'
    if flag_is_active(request, 'redesign'):
        template = 'results-redesign.html'

    return render(request, 'search/%s' % template, context)


@cache_page(60 * 15)  # 15 minutes.
def suggestions(request):
    """Return empty array until we restore internal search system."""

    mimetype = 'application/x-suggestions+json'

    term = request.GET.get('q')
    if not term:
        return HttpResponseBadRequest(mimetype=mimetype)

    results = []
    return HttpResponse(json.dumps(results), mimetype=mimetype)


@cache_page(60 * 60 * 168)  # 1 week.
def plugin(request):
    """Render an OpenSearch Plugin."""
    site = Site.objects.get_current()
    return render(request, 'search/plugin.html',
                        {'site': site, 'locale': request.locale},
                        content_type='application/opensearchdescription+xml')
