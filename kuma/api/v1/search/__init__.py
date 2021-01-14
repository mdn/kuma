from django.conf import settings
from django.http import JsonResponse
from elasticsearch import Elasticsearch, exceptions
from elasticsearch_dsl import Q, query, Search
from redo import retrying

from kuma.api.v1.decorators import allow_CORS_GET

from .forms import SearchForm


def legacy(request, locale=None):
    raise NotImplementedError("work harder")


@allow_CORS_GET
def search(request, locale=None):
    initial = {"size": 10, "page": 1, "archive": SearchForm.ARCHIVE_CHOICES[0]}
    if locale:
        initial["locale"] = locale
    form = SearchForm(request.GET, initial=initial)
    if not form.is_valid():
        return JsonResponse(form.errors.get_json_data(), status=400)

    locales = form.cleaned_data["locale"] or [settings.LANGUAGE_CODE]
    assert isinstance(locales, list)

    params = {
        "locales": [x.lower() for x in locales],
        "archive": form.cleaned_data["archive"],
        "query": form.cleaned_data["q"],
        "size": form.cleaned_data["size"],
        "page": form.cleaned_data["page"],
        "sort": form.cleaned_data["sort"],
    }
    from pprint import pprint

    pprint(params)

    # from elasticsearch_dsl import A
    # client = Elasticsearch(settings.ES_URLS)
    # search = Search(using=client, index=settings.SEARCH_INDEX_NAME)
    # agg = A("terms", field="locale", size=100)
    # # search = SongDoc.search()
    # search.aggs.bucket("per_locale", agg)
    # search = search[:0]  # select no hits
    # response = search.execute()
    # for each in response.aggregations.per_locale.buckets:
    #     print(each)

    results = _find(params)

    return JsonResponse(results)


def _find(params, total_only=False, make_suggestions=False, min_suggestion_score=0.8):
    client = Elasticsearch(settings.ES_URLS)
    search_query = Search(
        using=client,
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

    # XXX
    # The problem with multi_match is that it's not a phrase search
    # so searching for "javascript yibberish" will basically be the
    # same as searching for "javascript". And if you ask for suggestions
    # it'll probably come back with a (term) suggestion of
    # "javascript jibberish" which, yes, is different but still will just
    # result in what you would have gotten if you searched for "javascript".
    # The research to do is to see if it's better do use a boosted (OR) boolean
    # search with `match_phrase` and make that the primary strategy. Then,
    # only if nothing can be found, fall back to `multi_match`.
    # This choice of strategy should probably inform the use of suggestions too.
    # matcher = Q("multi_match", query=params["query"], fields=["title^10", "body"])
    sub_queries = []
    sub_queries.append(Q("match", title={"query": params["query"], "boost": 2.0}))
    sub_queries.append(Q("match", body={"query": params["query"], "boost": 1.0}))
    if " " in params["query"]:
        sub_queries.append(
            Q("match_phrase", title={"query": params["query"], "boost": 10.0})
        )
        sub_queries.append(
            Q("match_phrase", body={"query": params["query"], "boost": 5.0})
        )

        # sub_queries.append(Q("match_phrase", title=params["query"], boost=10.0))
        # sub_queries.append(Q("match_phrase", body=params["query"], boost=5.0))
    # matcher = query.Bool(should=sub_queries)
    sub_query = query.Bool(should=sub_queries)

    # matcher |= Q("match", query=params["query"], fields=["title^10", "body"])

    if params["locales"]:
        search_query = search_query.filter("terms", locale=params["locales"])
        # filters.append(Q("terms", locale=params["locales"]))
        # matcher &= Q("terms", locale=params["locales"])
        # search_query = search_query.query("bool", filter=[Q("terms", locale=params["locales"])
    if params["archive"] == "exclude":
        search_query = search_query.filter("term", archived=False)
    elif params["archive"] == "only":
        search_query = search_query.filter("term", archived=True)
        # filters.append(Q("term", archived=False))
        # matcher &= Q("term", archived=False)

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
            # query=query.Bool(should=[matcher]),
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
        from pprint import pprint

        pprint(search_query.to_dict())

    search_query = search_query.source(excludes=["body"])

    search_query = search_query[
        params["size"] * (params["page"] - 1) : params["size"] * params["page"]
    ]

    from pprint import pprint

    pprint(search_query.to_dict())
    retry_options = {
        "retry_exceptions": (
            # This is the standard operational exception.
            exceptions.ConnectionError,
            # This can happen if the search happened right as the index had
            # just been deleted due to a fresh re-indexing happening in Yari.
            exceptions.NotFoundError,
        ),
        # The default in redo is 60 seconds. Let's tone that down.
        "sleeptime": 1,
        "attempts": 5,
    }
    with retrying(search_query.execute, **retry_options) as retrying_function:
        response = retrying_function()

    if total_only:
        return response.hits.total

    metadata = {
        "took_ms": response.took,
        "total": response.hits.total,
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
                # XXX Oftentimes, when searching for phrases, like "WORD GOOBLYGOK"
                # Elasticsearch has already decided to ignore the "GOOBLYGOK" part,
                # and what you have so far is the 123 search results that exists
                # thanks to the "WORD" part. So if you re-attempt a search
                # for "WORD GOOBLYGOOK" (extra "O"), you'll still get the same
                # exact 123 search results.
                total = _find(params, total_only=True)
                if total["value"] > 0:
                    suggestions.append(
                        {
                            "text": string,
                            "total": total,
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
