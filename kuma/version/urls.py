from django.conf.urls import url

from . import views


urlpatterns = [
    # Serve the revision hashes.
    url(r"^media/revision.txt$", views.revision_hash, name="version.kuma"),
    url(
        r"^media/kumascript-revision.txt$",
        views.kumascript_revision_hash,
        name="version.kumascript",
    ),
]
