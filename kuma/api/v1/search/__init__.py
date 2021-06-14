from django import http
from django.conf import settings
from django.utils.cache import patch_cache_control
from elasticsearch import exceptions
from elasticsearch_dsl import Q, query, Search
from redo import retrying

from kuma.api.v1.decorators import allow_CORS_GET

from .forms import SearchForm

# This is the number of seconds to be put into the Cache-Control max-age header
# if the search is successful.
# We can increase the number as we feel more and more comfortable with how
# the `/api/v1/search` works.
SEARCH_CACHE_CONTROL_MAX_AGE = 60 * 60 * 12


class JsonResponse(http.JsonResponse):
    """The only reason this exists is so that other Django views can call
    views that return instances of this and then get to the data before it
    gets JSON serialized.
    This is something that rest_framework's JsonResponse supports.
    Ultimately, the only view that cares is the (old) Kuma search view page
    that calls the view function here in this file. Now it can do something like:

        response = kuma.api.v1.search.search(request)
        found = response.data

    """

    def __init__(self, data, *args, **kwargs):
        self.data = data
        super().__init__(data, *args, **kwargs)


def legacy(request, locale=None):
    raise NotImplementedError("work harder")


@allow_CORS_GET
def search(request, locale=None):
    initial = {"size": 10, "page": 1, "archive": SearchForm.ARCHIVE_CHOICES[0]}
    if locale:
        initial["locale"] = locale
    form = SearchForm(request.GET, initial=initial)
    if not form.is_valid():
        return JsonResponse({"errors": form.errors.get_json_data()}, status=400)

    locales = form.cleaned_data["locale"] or [settings.LANGUAGE_CODE]
    assert isinstance(locales, list)

    params = {
        "locales": [x.lower() for x in locales],
        "archive": form.cleaned_data["archive"],
        "query": form.cleaned_data["q"],
        "size": form.cleaned_data["size"],
        "page": form.cleaned_data["page"],
        "sort": form.cleaned_data["sort"],
        # The `slug` is always stored, as a Keyword index, in lowercase.
        "slug_prefixes": [x.lower() for x in form.cleaned_data["slug_prefix"]],
    }

    # By default, assume that we will try to make suggestions.
    make_suggestions = True
    if len(params["query"]) > 100 or max(len(x) for x in params["query"].split()) > 30:
        # For example, if it's a really long query, or a specific word is just too
        # long, you can get those tricky
        # TransportError(500, 'search_phase_execution_exception', 'Term too complex:
        # errors which are hard to prevent against.
        make_suggestions = False

    results = _find(
        params,
        make_suggestions=make_suggestions,
    )
    response = JsonResponse(results)

    # The reason for caching is that most of the time, the searches people make
    # are short and often stand a high chance of being reused by other users
    # in the CDN.
    # The worst that can happen is that we fill up the CDN with cached responses
    # that end up being stored there and never reused by another user.
    # We could consider only bothering with this based on looking at the parameters.
    # For example, if someone made a search with "complex parameters" we could skip
    # cache-control because it'll just be a waste to store it (CDN and client).
    # The reason for not using a "shared" cache-control, i.e. `s-max-age` is
    # because the cache-control seconds we intend to set are appropriate for both
    # the client and the CDN. If the value set is 3600 seconds, that means that
    # clients might potentially re-use their own browser cache if they trigger
    # a repeated search. And it's an appropriate number for the CDN too.
    # For more info about how our search patterns behave,
    # see https://github.com/mdn/kuma/issues/7799
    patch_cache_control(response, public=True, max_age=SEARCH_CACHE_CONTROL_MAX_AGE)
    return response


def _find(params, total_only=False, make_suggestions=False, min_suggestion_score=0.8):
    search_query = Search(
        index=settings.SEARCH_INDEX_NAME,
    )
    if make_suggestions:
        # XXX research if it it's better to use phrase suggesters and if
        # that works
        # https://www.elastic.co/guide/en/elasticsearch/reference/current/search-suggesters.html#phrase-suggester
        search_query = search_query.suggest(
            "title_suggestions", params["query"], term={"field": "title"}
        )
        search_query = search_query.suggest(
            "body_suggestions", params["query"], term={"field": "body"}
        )

    # The business logic here that we search for things different ways,
    # and each different way as a different boost which dictates its importance.
    # The importance order is as follows:
    #
    #  1. Title match-phrase
    #  2. Title match
    #  3. Body match-phrase
    #  4. Body match
    #
    # The order is determined by the `boost` number in the code below.
    # Remember that sort order is a combination of "match" and popularity, but
    # ideally the popularity should complement. Try to get a pretty good
    # sort by pure relevance first, and let popularity just make it better.
    #
    sub_queries = []
    sub_queries.append(Q("match", title={"query": params["query"], "boost": 5.0}))
    sub_queries.append(Q("match", body={"query": params["query"], "boost": 1.0}))
    if " " in params["query"]:
        sub_queries.append(
            Q("match_phrase", title={"query": params["query"], "boost": 10.0})
        )
        sub_queries.append(
            Q("match_phrase", body={"query": params["query"], "boost": 2.0})
        )

    sub_query = query.Bool(should=sub_queries)

    if params["locales"]:
        search_query = search_query.filter("terms", locale=params["locales"])
    if params["archive"] == "exclude":
        search_query = search_query.filter("term", archived=False)
    elif params["archive"] == "only":
        search_query = search_query.filter("term", archived=True)

    if params["slug_prefixes"]:
        sub_queries = [Q("prefix", slug=x) for x in params["slug_prefixes"]]
        search_query = search_query.query(query.Bool(should=sub_queries))

    search_query = search_query.highlight_options(
        pre_tags=["<mark>"],
        post_tags=["</mark>"],
        number_of_fragments=3,
        fragment_size=120,
        encoder="html",
    )
    search_query = search_query.highlight("title", "body")

    if params["sort"] == "relevance":
        search_query = search_query.sort("_score", "-popularity")
        search_query = search_query.query(sub_query)
    elif params["sort"] == "popularity":
        search_query = search_query.sort("-popularity", "_score")
        search_query = search_query.query(sub_query)
    else:
        popularity_factor = 10.0
        boost_mode = "sum"
        score_mode = "max"
        search_query = search_query.query(
            "function_score",
            query=sub_query,
            functions=[
                query.SF(
                    "field_value_factor",
                    field="popularity",
                    factor=popularity_factor,
                    missing=0.0,
                )
            ],
            boost_mode=boost_mode,
            score_mode=score_mode,
        )

    search_query = search_query.source(excludes=["body"])

    search_query = search_query[
        params["size"] * (params["page"] - 1) : params["size"] * params["page"]
    ]

    retry_options = {
        "retry_exceptions": (
            # This is the standard operational exception.
            exceptions.ConnectionError,
            # This can happen if the search happened right as the index had
            # just been deleted due to a fresh re-indexing happening in Yari.
            exceptions.NotFoundError,
            # This can happen when the index simply isn't ready yet.
            exceptions.TransportError,
        ),
        # The default in redo is 60 seconds. Let's tone that down.
        "sleeptime": settings.ES_RETRY_SLEEPTIME,
        "attempts": settings.ES_RETRY_ATTEMPTS,
        "jitter": settings.ES_RETRY_JITTER,
    }
    with retrying(search_query.execute, **retry_options) as retrying_function:
        response = retrying_function()

    if total_only:
        return response.hits.total

    metadata = {
        "took_ms": response.took,
        "total": {
            # The `response.hits.total` is a `elasticsearch_dsl.utils.AttrDict`
            # instance. Pluck only the exact data needed.
            "value": response.hits.total.value,
            "relation": response.hits.total.relation,
        },
        "size": params["size"],
        "page": params["page"],
    }
    documents = []
    for hit in response:
        try:
            body_highlight = list(hit.meta.highlight.body)
        except AttributeError:
            body_highlight = []
        try:
            title_highlight = list(hit.meta.highlight.title)
        except AttributeError:
            title_highlight = []

        d = {
            "mdn_url": hit.meta.id,
            "score": hit.meta.score,
            "title": hit.title,
            "locale": hit.locale,
            "slug": hit.slug,
            "popularity": hit.popularity,
            "archived": hit.archived,
            "summary": hit.summary,
            "highlight": {
                "body": body_highlight,
                "title": title_highlight,
            },
        }
        documents.append(d)

    try:
        suggest = getattr(response, "suggest")
    except AttributeError:
        suggest = None

    suggestions = []
    if suggest:
        suggestion_strings = _unpack_suggestions(
            params["query"],
            response.suggest,
            ("body_suggestions", "title_suggestions"),
        )

        for score, string in suggestion_strings:
            if score > min_suggestion_score or 1:
                # Sure, this is different way to spell, but what will it yield
                # if you actually search it?
                total = _find(dict(params, query=string), total_only=True)
                if total["value"] > 0:
                    suggestions.append(
                        {
                            "text": string,
                            "total": {
                                # This 'total' is an `AttrDict` instance.
                                "value": total.value,
                                "relation": total.relation,
                            },
                        }
                    )
                    # Since they're sorted by score, it's usually never useful
                    # to suggestion more than exactly 1 good suggestion.
                    break

    return {
        "documents": documents,
        "metadata": metadata,
        "suggestions": suggestions,
    }


def _unpack_suggestions(query, suggest, keys):
    alternatives = []
    for key in keys:
        for suggestion in getattr(suggest, key, []):
            for option in suggestion.options:
                alternatives.append(
                    (
                        option.score,
                        query[0 : suggestion.offset]
                        + option.text
                        + query[suggestion.offset + suggestion.length :],
                    )
                )
    alternatives.sort(reverse=True)  # highest score first
    return alternatives
