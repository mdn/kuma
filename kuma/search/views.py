from urllib.parse import parse_qs, urlencode

from django.conf import settings
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_GET
from django.views.generic import RedirectView
from ratelimit.decorators import ratelimit

from kuma.api.v1.search import search as search_api
from kuma.core.decorators import shared_cache_control


# Since the search endpoint accepts user input (via query parameters) and its
# response is compressed, use rate limiting to mitigate the BREACH attack
# (see http://breachattack.com/). It still needs to allow a user to click
# the filter switches (bug 1426968).
# Alternate: forbid gzip by setting Content-Encoding: identity
@never_cache
@require_GET
@ratelimit(key="user_or_ip", rate="25/m", block=True)
def search(request, *args, **kwargs):
    """
    The search view.

    --2021-- THIS VIEW IS A HACK! --2021--
    This Django view exists to server-side render the search results page.
    But we're moving the search result page to Yari and that one will use a XHR
    request (to /api/v1/search) from a skeleton page (aka. SPA).
    But as a way to get to that, we need to transition from the old to the new.
    So, this page uses the Django view in kuma.api.v1.search.search, which
    returns a special `JsonResponse` instance whose data we can pluck out
    to our needs for this old view.
    Once we've fully moved to the Yari (static + XHR to v1 API) site-search,
    we can comfortably delete this view.
    """
    # The underlying v1 API supports searching without a 'q' but the web
    # UI doesn't. For example, the search input field requires a value.
    # So we match that here too.
    if not request.GET.get("q", "").strip():
        status = 400
        context = {"results": {}}
    else:
        # TODO consider, if the current locale is *not* en-US, that we force
        # it to do a search in both locales.
        # This might come in handy for people searching in a locale where
        # there's very little results but they'd be happy to get the en-US ones.
        response = search_api(request, *args, **kwargs)
        results = response.data

        error = None
        status = response.status_code

        # Determine if there were validation errors
        if status == 400:
            error = ""
            for key, messages in results["errors"].items():
                for message in messages:
                    error += f"{key}: {message['message']}\n"
        else:
            # Have to rearrange the 'results' in a way the old search expects it.
            # ...which is as follows:
            #  - `count`: integer number of matched documents
            #  - `previous`: a URL or empty string
            #  - `next`: a URL or empty string
            #  - `query`: string
            #  - `start`: pagination number
            #  - `end`: pagination number
            #  - `documents`:
            #      - `title`
            #      - `locale`
            #      - `slug`
            #      - `excerpt`: string of safe HTML
            next_url = ""
            previous_url = ""
            page = results["metadata"]["page"]
            size = results["metadata"]["size"]
            count = results["metadata"]["total"]["value"]
            query_string = request.META.get("QUERY_STRING")
            query_string_parsed = parse_qs(query_string)
            if (page + 1) * size < count:
                query_string_parsed["page"] = f"{page + 1}"
                next_url = f"?{urlencode(query_string_parsed, True)}"
            if page > 1:
                if page == 2:
                    del query_string_parsed["page"]
                else:
                    query_string_parsed["page"] = f"{page - 1}"
                previous_url = f"?{urlencode(query_string_parsed, True)}"

            results = {
                "count": count,
                "next": next_url,
                "previous": previous_url,
                "query": request.GET.get("q"),
                "start": (page - 1) * size + 1,
                "end": page * size,
                "documents": [
                    {
                        "title": x["title"],
                        "slug": x["slug"],
                        "locale": x["locale"],
                        "excerpt": "<br>".join(x["highlight"].get("body", [])),
                    }
                    for x in results["documents"]
                ],
            }

        context = {"results": {"results": None if error else results, "error": error}}
    return render(request, "search/react.html", context, status=status)


class SearchRedirectView(RedirectView):
    permanent = True

    def get_redirect_url(self, *args, **kwargs):
        query_string = self.request.META.get("QUERY_STRING")
        url = reverse_lazy("api.v1.search")
        qs = parse_qs(query_string)
        # If you used `/en-Us/search.json` you can skip the `?locale=`
        # because the default locale in `/api/v1/search` is `en-US`.
        if self.request.LANGUAGE_CODE.lower() != settings.LANGUAGE_CODE.lower():
            qs["locale"] = self.request.LANGUAGE_CODE
        if qs:
            url += "?" + urlencode(qs, True)
        return url


@shared_cache_control(s_maxage=60 * 60 * 24 * 7)
def plugin(request):
    """Render an OpenSearch Plugin."""
    return render(
        request,
        "search/plugin.html",
        {"locale": request.LANGUAGE_CODE},
        content_type="application/opensearchdescription+xml",
    )
