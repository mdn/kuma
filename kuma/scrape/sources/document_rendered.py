"""DocumentRenderedSource requests MDN wiki documents."""
from __future__ import absolute_import, unicode_literals
import re

from django.utils.six.moves.urllib.parse import urlparse
from pyquery import PyQuery as pq

from .base import DocumentBaseSource


class DocumentRenderedSource(DocumentBaseSource):
    """
    Request the rendered document.

    This is used to detect zones and redirects.
    """

    # Regular expression for custom zone CSS, like zone-firefox.css
    re_custom_href = re.compile("""(?x)  # Verbose RE mode
        .*                # Match anything
        \/zone-           # Match '/zone-'
        (?P<slug>[^.]*)   # Capture the slug
        (\.[0-9a-fA-F]+)? # There may be a hash in the filename
        \.css             # Ends in .css
        """)

    def source_path(self):
        return '/%s/docs/%s' % (self.locale, self.slug)

    def load_prereqs(self, requester, storage):
        """Request the document, and process the redirects and response."""
        response = requester.request(self.source_path(),
                                     raise_for_status=False)
        if response.status_code not in (200, 301, 302):
            raise self.SourceError('status_code %s', response.status_code)
        data = {}

        # Is this a redirect?
        if response.history:
            redirect_from = urlparse(response.history[0].url).path
            redirect_to = urlparse(response.url).path
            if redirect_to != redirect_from:
                data['redirect_to'] = self.decode_href(redirect_to)

        # Is this a zone root?
        parsed = pq(response.content)
        body = parsed('body')
        if body.has_class('zone-landing'):
            data['is_zone_root'] = True

            # Find the zone stylesheet
            links = parsed('head link')
            for link in links:
                rel = link.attrib.get('rel')
                href = self.decode_href(link.attrib.get('href'))
                if rel == 'stylesheet' and href:
                    match = self.re_custom_href.match(href)
                    if match:
                        data['zone_css_slug'] = match.group('slug')

        return True, data

    def save_data(self, storage, data):
        """Save the rendered document data."""
        storage.save_document_rendered(self.locale, self.slug, data)
        return []
