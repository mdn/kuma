import bleach
import requests
from django.http import (
    Http404,
    HttpResponseBadRequest,
    HttpResponseForbidden,
    JsonResponse,
)
from django.middleware.csrf import get_token
from django.utils import timezone
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_http_methods
from ratelimit.decorators import ratelimit

from kuma.users.models import UserSubscription


BASE_URL = "http://docker.for.mac.host.internal:5000"

_hacky_cache = {}
_hacky_documents = {}


@never_cache
@ratelimit(key="user_or_ip", rate="100/m", block=True)
@require_http_methods(["GET", "POST"])
def document(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("not signed in")
    if not UserSubscription.objects.filter(user=user, canceled__isnull=True).exists():
        return HttpResponseForbidden("not a subscriber")

    url = (
        (request.GET.get("url") or "")
        .strip()
        .replace("https://developer.mozilla.org", "")
    )
    if not url:
        return HttpResponseBadRequest("missing 'url'")
    if not valid_url(url):
        return HttpResponseBadRequest("invalid 'url'")

    doc = get_document_from_url(url)

    notes = _hacky_cache.get(url, [])
    if request.method == "POST":
        text = (request.POST.get("text") or "").strip()
        if not text:
            return HttpResponseBadRequest("no 'text'")
        id = request.POST.get("id")
        if id:
            print(notes)
        else:

            text_html = text_to_html(text)

            now = convert_to_utc(timezone.now())
            notes.append(
                {
                    "id": notes and max(note["id"] for note in notes) + 1 or 1,
                    "text": text,
                    "created": now,
                    "modified": now,
                    "textHTML": text_html,
                    "url": url,
                    "title": doc["title"],
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


def text_to_html(text):
    html = bleach.clean(text, tags=[])
    html = html.replace("\n", "<br>\n")
    html = bleach.linkify(html)
    return html


def convert_to_utc(dt):
    """
    Given a timezone naive or aware datetime return it converted to UTC.
    """
    # Check if the given dt is timezone aware and if not make it aware.
    if timezone.is_naive(dt):
        default_timezone = timezone.get_default_timezone()
        dt = timezone.make_aware(dt, default_timezone)

    # Convert the datetime to UTC.
    return dt.astimezone(timezone.utc)


def valid_url(url):
    return url.startswith("/") and ("/docs/" in url or "/plus/" in url)


def get_document_from_url(url):
    if url not in _hacky_documents:
        abs_url = f"{BASE_URL}{url}/index.json"
        r = requests.get(abs_url)
        r.raise_for_status()
        data = r.json()
        _hacky_documents[url] = data["doc"]
    return _hacky_documents[url]


@never_cache
@ratelimit(key="user_or_ip", rate="100/m", block=True)
@require_http_methods(["GET"])
def all(request):
    user = request.user
    if not user.is_authenticated:
        return HttpResponseForbidden("not signed in")
    if not UserSubscription.objects.filter(user=user, canceled__isnull=True).exists():
        return HttpResponseForbidden("not a subscriber")
    all_notes = []

    all_notes = []
    for url, notes in _hacky_cache.items():
        for note in notes:
            all_notes.append(dict(note, url=url, title=_hacky_documents[url]["title"]))

    all_notes.sort(key=lambda note: note["modified"], reverse=True)

    context = {
        "notes": all_notes,
        "count": len(all_notes),
    }
    context["csrfmiddlewaretoken"] = get_token(request)
    return JsonResponse(context)


def is_subscriber(func):
    def inner(request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return HttpResponseForbidden("not signed in")
        if not UserSubscription.objects.filter(
            user=user, canceled__isnull=True
        ).exists():
            return HttpResponseForbidden("not a subscriber")
        return func(request, *args, **kwargs)

    return inner


@never_cache
@ratelimit(key="user_or_ip", rate="100/m", block=True)
@require_http_methods(["DELETE", "POST"])
@is_subscriber
def note(request, id):
    try:
        id = int(id)
    except ValueError:
        return HttpResponseBadRequest("not a valid ID")

    from pprint import pprint

    pprint(_hacky_cache)
    print("ID:", repr(id))
    for url, notes in _hacky_cache.items():
        found = False
        for note in notes:
            if note["id"] == id:
                found = True
                break
        if found:
            break
    else:
        return Http404(f"note {id} not found")

    if request.method == "DELETE":
        for url, notes in _hacky_cache.items():
            _hacky_cache[url] = [note for note in notes if note["id"] != id]
    else:
        text = (request.POST.get("text") or "").strip()
        if not text:
            return HttpResponseBadRequest("no 'text'")

        for url, notes in _hacky_cache.items():
            for note in notes:
                if note["id"] == id:
                    note["text"] = text
                    note["textHTML"] = text_to_html(text)

    return JsonResponse({"OK": True})
