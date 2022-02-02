from ninja import NinjaAPI
from ninja.errors import HttpError
from ratelimit.exceptions import Ratelimited

from .auth import admin_auth, subscriber_auth
from .plus.landing_page import api as landing_page_router
from .plus.notifications import (admin_router, notifications_router,
                                 watch_router)

api = NinjaAPI(auth=subscriber_auth, csrf=True, version="v1")
admin_api = NinjaAPI(
    auth=admin_auth, csrf=False, version="v1", urls_namespace="admin_api"
)

admin_api.add_router("/notifications/", admin_router)
api.add_router("/plus/notifications/", notifications_router)
api.add_router("/plus/", watch_router)
api.add_router("/plus/landing-page/", landing_page_router)


@api.exception_handler(Ratelimited)
def rate_limited(request, exc):
    return api.create_response(request, {"error": "Too many requests"}, status=429)
