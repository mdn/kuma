"""DocumentChildrenSource gathers child docs."""


from .base import DocumentBaseSource


class DocumentChildrenSource(DocumentBaseSource):
    """Recursively gather child docs ($children API)."""

    OPTIONS = {
        'depth': ('int_all', 0),    # Scrape the topic tree to this depth
        'revisions': ('int', 1),    # Gather this many revisions for each doc
        'translations': ('bool', False),  # Scrape the alternate translations
    }

    def source_path(self):
        return '/%s/docs/%s$children?depth=1' % (self.locale, self.slug)

    def load_and_validate_existing(self, storage):
        """Load child data from a previous gather."""
        child_data = storage.get_document_children(self.locale, self.slug)
        if child_data:
            children = self.extract_data(child_data)
            return True, children
        else:
            return False, []

    def load_prereqs(self, requester, storage):
        """Load one level of document child data from the $children API."""
        response = requester.request(self.source_path())
        data = response.json()
        return True, data

    def save_data(self, storage, data):
        """Save the raw child data, extract child documents."""
        storage.save_document_children(self.locale, self.slug, data)
        return self.extract_data(data)

    def extract_data(self, data):
        """Process child API data."""
        children = []
        if data['subpages']:
            new_opts = self.current_options()
            depth = new_opts.get('depth')
            if depth and depth != 'all':
                if depth == 1:
                    del new_opts['depth']
                else:
                    new_opts['depth'] -= 1
            for subpage in data['subpages']:
                url = self.decode_href(subpage['url'])
                children.append(('document', url, new_opts))
        return children
