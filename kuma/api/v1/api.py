from ninja import NinjaAPI
from ratelimit.exceptions import Ratelimited

from .auth import admin_auth, subscriber_auth

api = NinjaAPI(auth=subscriber_auth, csrf=True, version="v1")
admin_api = NinjaAPI(
    auth=admin_auth, csrf=False, version="v1", urls_namespace="admin_api"
)


@api.exception_handler(Ratelimited)
def rate_limited(request, exc):
    return api.create_response(request, {"error": "Too many requests"}, status=429)
