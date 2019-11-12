"""DocumentRedirectSource checks if a MDN wiki document is a redirect."""


from urllib.parse import urlparse

from .base import DocumentBaseSource


class DocumentRedirectSource(DocumentBaseSource):
    """Request the rendered document, to detect redirects."""

    def source_path(self):
        return '/%s/docs/%s' % (self.locale, self.slug)

    def load_prereqs(self, requester, storage):
        """Request the document, and process the redirects and response."""
        response = requester.request(self.source_path(),
                                     raise_for_status=False,
                                     method='HEAD')
        if response.status_code not in (200, 301, 302):
            raise self.SourceError('status_code %s', response.status_code)
        data = {}

        # Is this a redirect?
        if response.history:
            redirect_from = urlparse(response.history[0].url).path
            redirect_to = urlparse(response.url).path
            if redirect_to != redirect_from:
                data['redirect_to'] = self.decode_href(redirect_to)

        return True, data

    def save_data(self, storage, data):
        """Save the rendered document data."""
        storage.save_document_redirect(self.locale, self.slug, data)
        return []
