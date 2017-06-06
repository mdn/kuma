"""ZoneRootSource determine zone URL redirects."""
from __future__ import absolute_import, unicode_literals
import re
import logging

from django.utils.six.moves.urllib.parse import unquote

from .base import Source

logger = logging.getLogger('kuma.scraper')


class ZoneRootSource(Source):
    """Gather data about the root of a DocumentZone."""
    PARAM_NAME = 'path'
    re_path = re.compile(r"/(?P<locale>[^/]+)/(?P<zone_subpath>[^/]+)")

    def __init__(self, path, **options):
        super(ZoneRootSource, self).__init__(path, **options)
        if path != unquote(path):
            raise ValueError('URL-encoded path "%s"' % path)
        try:
            self.locale, self.slug = self.locale_and_zone(path)
        except ValueError as exception:
            self.locale, self.slug = None, None
            logger.warn(exception)
            self.state = self.STATE_ERROR

    def locale_and_zone(self, path):
        """Extract a document locale and zone subpath from a path."""
        match = self.re_path.match(path)
        if match:
            return match.groups()
        else:
            raise ValueError('Not a valid zoned document path "%s"' % path)

    def raise_if_errors(self, errors):
        """Raises errors to terminate zone processing."""
        if errors:
            raise self.SourceError('Bad JSON data for %s$json: %s',
                                   self.path, ', '.join(errors))

    def load_and_validate_existing(self, storage):
        """Load existing zone root data."""
        data = storage.get_zone_root(self.path)
        if data:
            self.raise_if_errors(data.get('errors'))
            return True, [('document', data['doc_path'], {})]
        else:
            return False, None

    def load_prereqs(self, requester, storage):
        """Scrape JSON data for the zone root."""
        response = requester.request(self.path + "$json")
        data = self.extract_data(response.json())
        return True, data

    def save_data(self, storage, data):
        """Save zone root for future processing."""
        storage.save_zone_root(self.path, data)
        self.raise_if_errors(data.get('errors'))
        return [('document', data['doc_path'], {})]

    def extract_data(self, metadata):
        """Extract zone root data from JSON."""
        err = []
        url = self.decode_href(metadata['url'])
        if url == self.path:
            err.append('url "%s" should be the non-zone path' % url)
        if metadata['locale'] != self.locale:
            err.append('locale "%s" should be the same as the path locale' %
                       metadata['locale'])
        if err:
            return {
                'errors': err,
                'doc_locale': self.locale,
                'metadata_locale': metadata['locale'],
                'metadata_url': url,
                'zone_path': self.path,
            }
        else:
            return {
                'doc_path': url,
                'zone_path': self.path,
            }
