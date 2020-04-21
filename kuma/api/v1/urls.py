from django.urls import path, re_path

from . import views


urlpatterns = [
    re_path(r"^doc/(?P<locale>[^/]+)/(?P<slug>.*)$", views.doc, name="api.v1.doc"),
    re_path(r"^whoami/?$", views.whoami, name="api.v1.whoami"),
    re_path(r"^search/(?P<locale>[^/]+)/?$", views.search, name="api.v1.search"),
    re_path(r"^bc-signal/?$", views.bc_signal, name="api.v1.bc_signal"),
    re_path(r"^users/(?P<username>[^/]+)/?$", views.get_user, name="api.v1.get_user"),
    path(
        "subscriptions/feedback/",
        views.send_subscriptions_feedback,
        name="api.v1.send_subscriptions_feedback",
    ),
    path("subscriptions/", views.subscriptions, name="api.v1.subscriptions"),
]
