"""RevisionSource scrapes historical wiki revisions."""
from __future__ import absolute_import, unicode_literals

import logging
import re

import dateutil

from kuma.core.utils import safer_pyquery as pq

from .base import DocumentBaseSource, Source

logger = logging.getLogger('kuma.scraper')


class RevisionSource(Source):
    """Import a historical wiki revision."""
    PARAM_NAME = 'path'
    OPTIONS = {
        'based_on': ('text', '')  # Revision this is based on
    }

    re_path = re.compile(r"""(?x) # Verbose mode
        /(?P<locale>[^/]+)        # Locale, like en-US
        /docs/                    # literal '/docs/'
        (?P<slug>[^$]*)           # Slug, like Mozilla/Firefox
        \$revision/               # literal '$revision/'
        (?P<revision_id>\d+)      # Revision ID
    """)

    def __init__(self, path, **options):
        """Parse and validate a revision path."""
        super(RevisionSource, self).__init__(path, **options)
        try:
            self.locale, self.slug, self.revision_id = self.split_path(path)
        except ValueError as exception:
            logger.warn(exception)
            self.state = self.STATE_ERROR

    @classmethod
    def split_path(cls, path):
        """Extract a revision parameters from a path."""
        match = cls.re_path.match(path)
        if match:
            locale, slug, raw_rev_id = match.groups()
            return locale, slug, int(raw_rev_id)
        else:
            raise ValueError('Not a valid revision path: %s' % path)

    def source_path(self):
        """Return MDN URL path for revision source."""
        return '/%s/docs/%s$revision/%d' % (self.locale, self.slug,
                                            self.revision_id)

    def load_and_validate_existing(self, storage):
        """Load existing revision data from storage."""
        self.document = storage.get_document(self.locale, self.slug)
        revision = storage.get_revision(self.revision_id)
        if revision and self.document:
            if revision.document == self.document:
                return True, []
            else:
                self.freshness = self.FRESH_NO
                raise self.SourceError(
                    'Revision %s is for Document "%s", expected "%s".',
                    self.revision_id,
                    revision.document.get_absolute_url(),
                    self.document.get_absolute_url())
        else:
            return False, []

    def load_prereqs(self, requester, storage):
        """Load document, meta, revision source, and creator."""
        needs = []
        doc_path = '/%s/docs/%s' % (self.locale, self.slug)

        # Load document, using pre-loaded if available
        if not getattr(self, 'document', None):
            self.document = storage.get_document(self.locale, self.slug)
        if not self.document:
            needs.append(('document', doc_path, {}))

        # Load document metadata
        meta = storage.get_document_metadata(self.locale, self.slug)
        if meta is None:
            options = {k: v for k, v in self.current_options().items()
                       if k in DocumentBaseSource.STANDARD_DOC_OPTIONS}
            needs.append(('document_meta', doc_path, options))

        # Load revision HTML
        path = self.source_path()
        rev_source = storage.get_revision_html(path)
        if not rev_source:
            response = requester.request(path, raise_for_status=False)
            if response.status_code != 200:
                raise self.SourceError('status_code %s', response.status_code)
            rev_source = response.content
            storage.save_revision_html(path, rev_source)
        data = self.extract_data(rev_source)

        # Load revision creator
        creator_username = data.pop('creator')
        creator = storage.get_user(creator_username)
        if not creator:
            needs.append(('user', creator_username, {}))

        # Load revision this is based on
        if self.based_on:
            b_locale, b_slug, b_id = self.split_path(self.based_on)
            based_rev = storage.get_revision(b_id)
            if not based_rev:
                needs.append(('revision', self.based_on, {}))

        if needs:
            return False, {'needs': needs}
        else:
            data['id'] = self.revision_id
            data['creator'] = creator
            data['document'] = self.document
            if data['is_current'] and data['slug'] != self.document.slug:
                logger.warn('Current revision %d has slug "%s". Setting'
                            ' to document slug "%s".',
                            self.revision_id, data['slug'],
                            self.document.slug)
                data['slug'] = self.document.slug
            if data['is_current']:
                data['review_tags'] = meta.get('review_tags', [])
                data['localization_tags'] = meta.get('localization_tags', [])
            if self.based_on:
                data['based_on_id'] = based_rev.id
            return True, data

    def save_data(self, storage, data):
        """Save the extracted revision data."""
        storage.save_revision(data)
        return []

    def extract_data(self, html):
        """Extract revision source and metadata from HTML."""
        data = {}
        keys = ('slug', 'title', 'id', 'created', 'creator', 'is_current',
                'comment')
        parsed = pq(html)

        # Parse revision-info list
        for key in keys:
            name = key.replace('_', '-')
            span = parsed('span[data-name="%s"]' % name)
            if key == 'id':
                value = int(span.text())
            elif key == 'created':
                created = span[0].cssselect('time')[0].attrib['datetime']
                value = dateutil.parser.parse(created)
                value = value.replace(tzinfo=None)
            elif key == 'is_current':
                value = span.attr['data-value'] == '1'
            elif key == 'comment':
                value = span.text() or ''
            else:
                value = span.text()
            data[key] = value

        # Parse tags
        tags = []
        tag_links = parsed.find('ul.tags li a')
        for tag_link in tag_links:
            tags.append(tag_link.text)
        data['tags'] = tags

        # Revision content
        source_elem = parsed.find('div#doc-source pre')[0]
        data['content'] = source_elem.text

        return data
        return data
