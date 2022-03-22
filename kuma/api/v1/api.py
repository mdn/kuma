from django.http import HttpResponse
from django.utils.cache import add_never_cache_headers
from ninja import NinjaAPI
from ratelimit.exceptions import Ratelimited

from .auth import admin_auth, profile_auth


class NoCacheNinjaAPI(NinjaAPI):
    def create_response(self, *args, **kwargs) -> HttpResponse:
        response = super().create_response(*args, **kwargs)
        add_never_cache_headers(response)
        return response


api = NoCacheNinjaAPI(auth=profile_auth, csrf=True, version="v1")

admin_api = NoCacheNinjaAPI(
    auth=admin_auth, csrf=False, version="v1", urls_namespace="admin_api"
)


@api.exception_handler(Ratelimited)
def rate_limited(request, exc):
    return api.create_response(request, {"error": "Too many requests"}, status=429)
