"""DocumentSource scrapes MDN wiki documents."""
from __future__ import absolute_import, unicode_literals
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
                         self.revisions == 1 and
                         self.normalized_path)
        if not self.force and just_this_doc:
            document = storage.get_document(self.locale, self.slug)
            if document:
                return True, []
        return False, []

    def load_prereqs(self, requester, storage):
        """Load the data needed for a document."""
        data = {'needs': []}

        # Load data, gathering further source needs
        self.load_prereq_normalized_path(storage, data)
        if self.normalized_path:
            self.load_prereq_parent_topic(storage, data)
            self.load_prereq_rendered(storage, data)
            if data.get('has_rendered'):
                self.load_prereq_redirect(storage, data)
            if data.get('is_standard_page'):
                self.load_prereq_metadata(storage, data)
                self.load_prereq_english_parent(storage, data)
                self.load_prereq_history(storage, data)
                self.load_prereq_children(storage, data)

        return not data['needs'], data

    def load_prereq_normalized_path(self, storage, data):
        """Load zone data to normalize path, if needed."""
        if self.normalized_path:
            return  # Already normalized, done

        # Determine the standard path associated with the zone
        zone_data = storage.get_zone_root(self.path)
        if zone_data is None:
            data['needs'].append(('zone_root', self.path, {}))
        elif zone_data.get('errors'):
            raise self.SourceError(
                'Unable to load zone root for %s', self.path)
        else:
            self.normalized_path = self.path.replace(
                zone_data['zone_path'], zone_data['doc_path'])
            self.locale, self.slug = self.locale_and_slug(
                self.normalized_path)

    def load_prereq_parent_topic(self, storage, data):
        """Load the parent topic, if a child page."""
        assert self.normalized_path
        if not self.parent_slug:
            return  # No parent to load

        parent_topic = storage.get_document(self.locale, self.parent_slug)
        if parent_topic is None:
            data['needs'].append(('document', self.parent_path, {}))
        else:
            data['parent_topic'] = parent_topic

    def load_prereq_rendered(self, storage, data):
        """Load the rendered page, to detect redirects and zones."""
        assert self.normalized_path
        rendered = storage.get_document_rendered(self.locale, self.slug)
        if rendered is None:
            data['needs'].append(
                ('document_rendered', self.normalized_path, {}))
        else:
            data['has_rendered'] = True
            data['redirect_to'] = rendered.get('redirect_to')
            data['is_zone_root'] = rendered.get('is_zone_root', False)
            data['zone_css_slug'] = rendered.get('zone_css_slug', '')

    def load_prereq_redirect(self, storage, data):
        """Load the zone or standard redirect."""
        assert self.normalized_path
        data['is_standard_page'] = data.get('has_rendered')
        redirect_to = data.get('redirect_to')
        if not redirect_to:
            return  # Not a redirect, don't follow

        # Is it a zoned URL or a moved page?
        try:
            rd_locale, rd_slug = self.locale_and_slug(redirect_to)
        except ValueError:
            # Zoned URL
            zone_redirect = storage.get_zone_root(redirect_to)
            if zone_redirect is None:
                data['needs'].append(('zone_root', redirect_to, {}))
            elif zone_redirect.get('errors'):
                raise self.SourceError('Unable to get zone_root "%s"',
                                       redirect_to)
            else:
                data['zone_redirect_path'] = zone_redirect['zone_path']
                z_path = zone_redirect['doc_path']
                if z_path != self.path:
                    z_locale, z_slug = self.locale_and_slug(z_path)
                    zone_root_doc = storage.get_document(z_locale, z_slug)
                    if zone_root_doc is None:
                        data['needs'].append(('document', z_path, {}))
        else:
            # Moved Page
            redirect = storage.get_document(rd_locale, rd_slug)
            data['is_standard_page'] = False
            if redirect is None:
                data['needs'].append(('document', redirect_to, {}))

    def load_prereq_metadata(self, storage, data):
        """Load the document metadata."""
        assert self.normalized_path
        meta = storage.get_document_metadata(self.locale, self.slug)
        if meta is None:
            data['needs'].append(('document_meta', self.normalized_path,
                                 self.current_options()))
        elif 'error' in meta:
            raise self.SourceError('Error getting metadata for %s',
                                   self.normalized_path)
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
            data['needs'].append(('document_history', self.normalized_path,
                                 {"revisions": self.revisions}))
        elif len(history) == 0:
            raise self.SourceError('Empty history for document "%s"',
                                   self.normalized_path)

    def load_prereq_children(self, storage, data):
        """Load the document children."""
        if self.depth == 0:
            return
        children = storage.get_document_children(self.locale, self.slug)
        if children is None:
            options = self.current_options()
            data['needs'].append(('document_children', self.normalized_path,
                                  options))

    def save_data(self, storage, data):
        """Save the document as a redirect or full document."""
        redirect_to = data.get('redirect_to')
        if redirect_to and not data.get('zone_redirect_path'):
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
                'is_zone_root',
                'locale',
                'modified',
                'parent',
                'parent_topic',
                'slug',
                'tags',
                'title',
                'uuid',
                'zone_css_slug',
                'zone_redirect_path',
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
        return [('document_current', self.normalized_path,
                 {'revisions': self.revisions})]
