"""DocumentCurrent checks that the current revision is scraped."""


import logging

from .base import DocumentBaseSource
from .revision import RevisionSource

logger = logging.getLogger('kuma.scraper')


class DocumentCurrentSource(DocumentBaseSource):
    """
    Ensure the current revision is scraped.

    For some documents, such as page moves, the latest revision is not the
    current revision. Usually the second-to-latest is.
    """

    OPTIONS = {
        'revisions': ('int', 1),  # Scrape this many past revisions
    }

    def load_prereqs(self, requester, storage):
        """Check if current revision is in loaded revisions."""
        doc = storage.get_document(self.locale, self.slug)
        if doc and doc.current_revision:
            return True, []  # Document has a current revision, we're done

        # Are all the requested revisions loaded?
        data = storage.get_document_history(self.locale, self.slug)
        if not data:
            return False, {'needs': [('document_history', self.path,
                                      {'revisions': self.revisions})]}
        needed = []
        for src_type, href, params in data['revisions'][:self.revisions]:
            locale, slug, rev_id = RevisionSource.split_path(href)
            rev = storage.get_revision(rev_id)
            if rev is None:
                needed.append((src_type, href, params))
        if needed:
            return False, {'needs': needed}  # Wait for revisions to load
        if data['is_all']:
            raise self.SourceError('No current_revision found for document.')

        # Ask for one more revision for the document
        # The common case is that the second-to-most-recent revision is the
        # current revision (just before a page move)
        next_srcs = [
            ('document', self.path, {'revisions': self.revisions + 1})]

        if len(data['revisions']) > self.revisions:
            # Pre-request the next revision, to help avoid dependency block
            next_srcs.append(data['revisions'][self.revisions])
        else:
            # Pre-request 2x revisions, to avoid dependency block detection
            # and avoid Shlemiel the painter's algorithm.
            next_srcs.append(('document_history', self.path,
                              {'revisions': len(data['revisions']) * 2}))
        return False, {'needs': next_srcs}

    def save_data(self, storage, data):
        """Nothing to save for this source, no next sources."""
        return []
