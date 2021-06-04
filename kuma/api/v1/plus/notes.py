import datetime

from django.http import HttpResponseBadRequest, HttpResponseForbidden, JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from ratelimit.decorators import ratelimit


_hacky_cache = {}


@never_cache
@ratelimit(key="user_or_ip", rate="100/m", block=True)
@require_http_methods(["GET", "POST"])
def document(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("not signed in")

    url = (
        (request.GET.get("url") or "")
        .strip()
        .replace("https://developer.mozilla.org", "")
    )
    if not url:
        return HttpResponseBadRequest("missing 'url'")
    if not valid_url(url):
        return HttpResponseBadRequest("invalid 'url'")

    notes = _hacky_cache.get(url, [])
    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        if not text:
            return HttpResponseBadRequest("no 'text'")
        id = request.POST.get("id")
        if id:
            print(notes)
        else:
            notes.append(
                {
                    "id": len(notes),
                    "text": text,
                    "created": datetime.datetime.utcnow(),
                    "modified": datetime.datetime.utcnow(),
                    "textRendered": text,  # XXX urlify
                    "url": url,
                }
            )
            _hacky_cache[url] = notes
            return JsonResponse({"OK": True})

    context = {
        "notes": notes,
        "count": len(notes),
    }
    context["csrfmiddlewaretoken"] = get_token(request)
    return JsonResponse(context)


def valid_url(url):
    return url.startswith("/") and ("/docs/" in url or "/plus/" in url)
