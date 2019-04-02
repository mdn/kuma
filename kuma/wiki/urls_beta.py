from django.conf.urls import url

from . import views
from .constants import DOCUMENT_PATH_RE


urlpatterns = [
    url(r'^(?P<document_path>%s)$' % DOCUMENT_PATH_RE.pattern,
        views.document.react_document,
        name='wiki.document')
]
