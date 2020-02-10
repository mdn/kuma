"""DocumentHistorySource scrapes the wiki history page."""


import logging

from kuma.core.utils import safer_pyquery as pq

from .base import DocumentBaseSource

logger = logging.getLogger("kuma.scraper")


class DocumentHistorySource(DocumentBaseSource):
    """Gather the revision data for an MDN Document."""

    OPTIONS = {
        "revisions": ("int", 1),  # Scrape this many past revisions
    }

    def source_path(self):
        """Get MDN path for the document history."""
        path = "/%s/docs/%s$history" % (self.locale, self.slug)
        if self.revisions > 1:
            path += "?limit=%d" % self.revisions
        return path

    def load_and_validate_existing(self, storage):
        """Load history data from a previous operation."""
        data = storage.get_document_history(self.locale, self.slug)
        if data and len(data["revisions"]) >= self.revisions:
            requested_revisions = data["revisions"][: self.revisions]
            requested_revisions.reverse()
            return True, requested_revisions
        else:
            return False, []

    def load_prereqs(self, requester, storage):
        """Load history data from the server."""
        path = self.source_path()
        response = requester.request(path, raise_for_status=False)
        if response.status_code == 200:
            return True, response.content
        else:
            raise self.SourceError("status_code %s", response.status_code)

    def save_data(self, storage, data):
        """Extract revisions and save for next call."""
        revs = self.extract_data(data)
        is_all = len(revs) < self.revisions
        data = {"revisions": revs, "is_all": is_all}
        storage.save_document_history(self.locale, self.slug, data)
        requested_revisions = revs[: self.revisions]
        requested_revisions.reverse()
        return requested_revisions

    def extract_data(self, content):
        """Convert a history pageview into history data."""
        revs = []
        parsed = pq(content)

        # If translation, there may be an entry for the English source
        en_source = parsed.find(
            "li.revision-list-en-source" " div.revision-list-date a"
        )
        if en_source:
            en_href = self.decode_href(en_source[0].attrib["href"])
        else:
            en_href = None

        for link in parsed.find("div.revision-list-date a"):
            href = self.decode_href(link.attrib["href"])
            if href == en_href:
                revs[-1][-1]["based_on"] = en_href
            else:
                revs.append(("revision", href, {}))
        return revs
