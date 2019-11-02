"""DocumentSource scrapes MDN wiki documents."""


import logging

import dateutil

from .base import DocumentBaseSource

logger = logging.getLogger('kuma.scraper')


class DocumentSource(DocumentBaseSource):
    """Coordinate scraping and local cloning of an MDN Document."""

    OPTIONS = DocumentBaseSource.STANDARD_DOC_OPTIONS

    def load_and_validate_existing(self, storage):
        """Load the document from storage in simple cases."""
        just_this_doc = (not self.translations and
                         self.depth == 0 and
                         self.revisions == 1)
        if not self.force and just_this_doc and self.locale and self.slug:
            document = storage.get_document(self.locale, self.slug)
            if document:
                return True, []
        return False, []

    def load_prereqs(self, requester, storage):
        """Load the data needed for a document."""
        data = {'needs': []}

        if self.locale is None and self.slug is None:
            raise self.SourceError('Not a document path "%s"', self.path)

        # Load data, gathering further source needs
        self.load_prereq_parent_topic(storage, data)
        self.load_prereq_redirect_check(storage, data)
        if data.get('has_redirect_check'):
            self.load_prereq_redirect(storage, data)
        if data.get('is_standard_page'):
            self.load_prereq_metadata(storage, data)
            self.load_prereq_english_parent(storage, data)
            self.load_prereq_history(storage, data)
            self.load_prereq_children(storage, data)

        return not data['needs'], data

    def load_prereq_parent_topic(self, storage, data):
        """Load the parent topic, if a child page."""
        if not self.parent_slug:
            return  # No parent to load

        parent_topic = storage.get_document(self.locale, self.parent_slug)
        if parent_topic is None:
            data['needs'].append(('document', self.parent_path, {}))
        else:
            data['parent_topic'] = parent_topic

    def load_prereq_redirect_check(self, storage, data):
        """Check the URL for redirects."""
        redirect = storage.get_document_redirect(self.locale, self.slug)
        if redirect is None:
            data['needs'].append(('document_redirect', self.path, {}))
        else:
            data['has_redirect_check'] = True
            data['redirect_to'] = redirect.get('redirect_to')

    def load_prereq_redirect(self, storage, data):
        """Load the destination of a redirect."""
        data['is_standard_page'] = data.get('has_redirect_check')
        redirect_to = data.get('redirect_to')
        if not redirect_to:
            return  # Not a redirect, don't follow

        # Load the destination page
        rd_locale, rd_slug = self.locale_and_slug(redirect_to)
        redirect = storage.get_document(rd_locale, rd_slug)
        data['is_standard_page'] = False
        if redirect is None:
            data['needs'].append(('document', redirect_to, {}))

    def load_prereq_metadata(self, storage, data):
        """Load the document metadata."""
        meta = storage.get_document_metadata(self.locale, self.slug)
        if meta is None:
            data['needs'].append(('document_meta', self.path,
                                 self.current_options()))
        elif 'error' in meta:
            raise self.SourceError('Error getting metadata for %s', self.path)
        elif meta:
            data['id'] = meta['id']
            data['locale'] = meta['locale']
            data['modified'] = dateutil.parser.parse(meta['modified'])
            data['slug'] = meta['slug']
            data['tags'] = meta['tags']
            data['title'] = meta['title']
            data['translations'] = meta['translations']

            # Redirects don't have UUIDs
            if 'uuid' in meta:
                data['uuid'] = meta['uuid']
            else:
                logger.warning('No uuid: %s', self.path)

    def load_prereq_english_parent(self, storage, data):
        """Load the English parent, if this is a translation."""
        if self.locale == 'en-US':
            return  # No English parent for English docs
        if 'translations' not in data:
            return  # Metadata not loaded yet

        # For translations - have we loaded the English document?
        for translation in data['translations']:
            if translation['locale'] == 'en-US':
                en_path = self.decode_href(translation['url'])
                try:
                    en_locale, en_slug = self.locale_and_slug(en_path)
                except ValueError:
                    raise self.SourceError(
                        'Invalid meta for "%s": In translations,'
                        ' invalid path "%s" for "en-US"',
                        self.path, en_path)
                else:
                    en_doc = storage.get_document(en_locale, en_slug)
                    if en_doc is None:
                        data['needs'].append(('document', en_path, {}))
                    else:
                        data['parent'] = en_doc

    def load_prereq_history(self, storage, data):
        """Load the revision history."""
        history = storage.get_document_history(self.locale, self.slug)
        if history is None:
            data['needs'].append(('document_history', self.path,
                                 {"revisions": self.revisions}))
        elif len(history) == 0:
            raise self.SourceError('Empty history for document "%s"',
                                   self.path)

    def load_prereq_children(self, storage, data):
        """Load the document children."""
        if self.depth == 0:
            return
        children = storage.get_document_children(self.locale, self.slug)
        if children is None:
            options = self.current_options()
            data['needs'].append(('document_children', self.path, options))

    def save_data(self, storage, data):
        """Save the document as a redirect or full document."""
        redirect_to = data.get('redirect_to')
        if redirect_to:
            # Prepare data for a redirect document
            doc_data = {
                'locale': self.locale,
                'slug': self.slug,
                'redirect_to': redirect_to
            }
        else:
            # Prepare data for a full document
            keys = (
                'id',
                'locale',
                'modified',
                'parent',
                'parent_topic',
                'slug',
                'tags',
                'title',
                'uuid',
            )
            doc_data = {}
            for key in keys:
                if key in data:
                    doc_data[key] = data[key]
            if doc_data['slug'] != self.slug:
                logger.warn(
                    'Meta slug "%s" does not match slug for "%s".',
                    doc_data['slug'], self.path)
                doc_data['slug'] = self.slug
            if doc_data['locale'] != self.locale:
                logger.warn(
                    'Meta locale "%s" does not match locale for "%s".',
                    doc_data['locale'], self.path)
                doc_data['locale'] = self.locale
        storage.save_document(doc_data)
        return [('document_current', self.path,
                 {'revisions': self.revisions})]
