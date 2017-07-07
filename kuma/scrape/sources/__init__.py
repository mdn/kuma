"""Data sources for scraping MDN."""
from __future__ import absolute_import, unicode_literals

from .base import DocumentBaseSource, Source
from .document import DocumentSource
from .document_children import DocumentChildrenSource
from .document_current import DocumentCurrentSource
from .document_history import DocumentHistorySource
from .document_meta import DocumentMetaSource
from .document_rendered import DocumentRenderedSource
from .links import LinksSource
from .revision import RevisionSource
from .user import UserSource
from .zone_root import ZoneRootSource

__all__ = [
    DocumentBaseSource,
    DocumentChildrenSource,
    DocumentCurrentSource,
    DocumentHistorySource,
    DocumentMetaSource,
    DocumentRenderedSource,
    DocumentSource,
    LinksSource,
    RevisionSource,
    Source,
    UserSource,
    ZoneRootSource,
]
