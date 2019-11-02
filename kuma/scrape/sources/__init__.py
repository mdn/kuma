"""Data sources for scraping MDN."""


from .base import DocumentBaseSource, Source
from .document import DocumentSource
from .document_children import DocumentChildrenSource
from .document_current import DocumentCurrentSource
from .document_history import DocumentHistorySource
from .document_meta import DocumentMetaSource
from .document_redirect import DocumentRedirectSource
from .links import LinksSource
from .revision import RevisionSource
from .user import UserSource

__all__ = [
    DocumentBaseSource,
    DocumentChildrenSource,
    DocumentCurrentSource,
    DocumentHistorySource,
    DocumentMetaSource,
    DocumentRedirectSource,
    DocumentSource,
    LinksSource,
    RevisionSource,
    Source,
    UserSource,
]
