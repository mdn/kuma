from django.urls import path

from . import search
from .api import api
from .plus.bookmarks import router as bookmarks_router
from .plus.landing_page import router as landing_page_router
from .plus.notifications import notifications_router, watch_router
from .views import settings_router

api.add_router("/settings", settings_router)
api.add_router("/plus/notifications/", notifications_router)
api.add_router("/plus/", watch_router)
api.add_router("/plus/collection/", bookmarks_router)
api.add_router("/plus/landing-page/", landing_page_router)

urlpatterns = [
    path("", api.urls),
    path("search/<locale>", search.search, name="api.v1.search_legacy"),
    path("search", search.search, name="api.v1.search"),
]
