import re

from django.urls import include, re_path

from .views import code


DOCUMENT_PATH_RE = re.compile(r"[^\$]+")


# These patterns inherit (?P<document_path>[^\$]+).
document_patterns = [
    re_path(
        r"^\$samples/(?P<sample_name>.+)/files/(?P<attachment_id>\d+)/(?P<filename>.+)$",
        code.raw_code_sample_file,
        name="wiki.raw_code_sample_file",
    ),
    re_path(
        r"^\$samples/(?P<sample_name>.+)$",
        code.code_sample,
        name="wiki.code_sample",
    ),
]

lang_urlpatterns = [
    re_path(
        r"^(?P<document_path>%s)" % DOCUMENT_PATH_RE.pattern, include(document_patterns)
    ),
]
