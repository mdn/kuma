"""LinksSource gathers wiki document links from a rendered page."""



import logging
from urllib.parse import urlparse

from django.conf import settings

from kuma.core.utils import safer_pyquery as pq

from .base import Source

logger = logging.getLogger('kuma.scraper')


class LinksSource(Source):
    """Gather document links from a rendered page for scraping.

    Links are scraped from the header, footer, and content. Links that look
    like documents are queued for download. This will not include the current
    page, which should be requested with a DocumentSource if applicable.
    """

    OPTIONS = {
        'depth': ('int_all', 0),          # Scrape the topic tree to this depth
        'revisions': ('int', 1),          # Scrape this many past revisions
        'translations': ('bool', False),  # Scrape the alternate translations
    }

    PARAM_NAME = 'path'

    ignored_slugs = {
        'dashboards',
        'profiles',
        'search',
        'users/signin',
        'docs/tag/',
    }

    def __init__(self, path=None, **options):
        """Process and validate the initial path."""
        if (not path) or (path == '/'):
            path = '/en-US/'  # Default to English homepage
        path = urlparse(path).path
        assert path.startswith('/')
        self.locale = path.split('/')[1]
        assert self.locale in settings.ENABLED_LOCALES
        super(LinksSource, self).__init__(path, **options)

    def load_prereqs(self, requester, storage):
        """Request the page and gather document links."""
        response = requester.request(self.path)
        parsed = pq(response.content)
        options = self.current_options()
        requirements = []
        seen_paths = set()

        for link in parsed('a'):
            doc_path = self.doc_path_for_href(link.attrib.get('href', ''))
            if doc_path and doc_path not in seen_paths:
                seen_paths.add(doc_path)
                requirements.append(('document', doc_path, options))

        return True, requirements

    def doc_path_for_href(self, href):
        """
        Return a Document path for the given <a href="url">.

        If the href doesn't look like a wiki document, then return None.
        """
        href = self.decode_href(href)
        path = urlparse(href).path

        # Strip trailing slashes
        if path.endswith('/'):
            path = path[:-1]

        # Skip anchors and non-absolute links
        # The URLAbsolutionFilter should convert to absolute links
        if not path.startswith('/'):
            return

        # Skip API endpoints
        if '$' in path:
            return

        # Skip other locales, non-translated pages, and the homepage
        if not path.startswith('/' + self.locale + '/'):
            return

        # Skip known non-wiki documents
        slug = path.split('/', 2)[2]
        if any([slug.startswith(ignore) for ignore in self.ignored_slugs]):
            return

        return path

    def save_data(self, storage, data):
        """Return the links on the page as post-sources."""
        return data
