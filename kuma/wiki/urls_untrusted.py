from django.urls import include, re_path

from . import views
from .constants import DOCUMENT_PATH_RE


# These patterns inherit (?P<document_path>[^\$]+).
document_patterns = [
    re_path(
        r"^\$samples/(?P<sample_name>.+)/files/(?P<attachment_id>\d+)/(?P<filename>.+)$",
        views.code.raw_code_sample_file,
        name="wiki.raw_code_sample_file",
    ),
    re_path(
        r"^\$samples/(?P<sample_name>.+)$",
        views.code.code_sample,
        name="wiki.code_sample",
    ),
]

lang_urlpatterns = [
    re_path(
        r"^(?P<document_path>%s)" % DOCUMENT_PATH_RE.pattern, include(document_patterns)
    ),
]
