from django.conf.urls import include, url

from . import views
from .constants import DOCUMENT_PATH_RE


# These patterns inherit (?P<document_path>[^\$]+).
document_patterns = [
    url(
        r"^\$samples/(?P<sample_name>.+)/files/(?P<attachment_id>\d+)/(?P<filename>.+)$",
        views.code.raw_code_sample_file,
        name="wiki.raw_code_sample_file",
    ),
    url(
        r"^\$samples/(?P<sample_name>.+)$",
        views.code.code_sample,
        name="wiki.code_sample",
    ),
]

lang_urlpatterns = [
    url(
        r"^(?P<document_path>%s)" % DOCUMENT_PATH_RE.pattern, include(document_patterns)
    ),
]
