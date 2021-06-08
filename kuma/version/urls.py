from django.urls import re_path

from . import views


urlpatterns = [
    # Serve the revision hashes.
    re_path(r"^media/revision.txt$", views.revision_hash, name="version.kuma"),
]
