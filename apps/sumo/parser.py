from django.utils.http import urlquote

import wikimarkup
import jingo

from settings import WIKI_UPLOAD_URL
from .models import WikiPage


ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'class'],
    'div': ['id', 'class'],
    'h1': ['id'],
    'h2': ['id'],
    'h3': ['id'],
    'h4': ['id'],
    'h5': ['id'],
    'h6': ['id'],
    'li': ['class'],
    'span': ['class'],
    'img': ['src', 'alt', 'title', 'height', 'width'],
}


class WikiParser(object):
    """
    Wrapper for wikimarkup. Adds Kitsune-specific callbacks and setup.
    """

    def __init__(self):
        # Register this hook so it gets called
        self.wikimarkup = wikimarkup
        wikimarkup.registerInternalLinkHook(None, self.hookInternalLink)
        wikimarkup.registerInternalLinkHook('Image', self.hookImageTag)

    def parse(self, text, showToc=True):
        return self.wikimarkup.parse(
            text, showToc, attributes=ALLOWED_ATTRIBUTES)

    def _getWikiLink(self, link):
        """
        Checks the page exists, and returns its URL, or the URL to create it.
        """
        try:
            return WikiPage.objects.get(pageName=link).get_url()
        except WikiPage.DoesNotExist:
            return WikiPage.get_create_url(link)

    def hookInternalLink(self, parser, space, name):
        """Parses text and returns internal link."""
        link = name
        text = name

        # Split on pipe -- [[href|name]]
        separator = name.find('|')
        if separator != -1:
            link, text = link.split('|', 1)

        hash_pos = link.find('#')
        hash = ''
        if hash_pos != -1:
            link, hash = link.split('#', 1)

        # Sections use _, page names use +
        if hash != '':
            hash = '#' + hash.replace(' ', '_')

        # Links to this page can just contain href="#hash"
        if link == '' and hash != '':
            return u'<a href="%s">%s</a>' % (hash, text)

        link = self._getWikiLink(link)
        return u'<a href="%s%s">%s</a>' % (link, hash, text)

    def _getImagePath(self, link):
        """Returns an uploaded image's path for image paths in markup."""
        return WIKI_UPLOAD_URL + urlquote(link)

    def _buildImageParams(self, items):
        """
        Builds a list of items and return image-relevant parameters in a dict.
        """
        params = {}
        # Empty items returns empty params
        if not items:
            return params

        for item in items:
            if item.find('=') != -1:
                param, value = item.split('=', 1)
                params[param] = value
            else:
                params[item] = False

        if 'page' in params and params['page']:
            params['link'] = self._getWikiLink(params['page'])

        return params

    def hookImageTag(self, parser, space, name):
        """Adds syntax for inserting images."""
        link = name
        caption = name
        params = {}

        # Parse the inner syntax, e.g. [[Image:src|option=val|caption]]
        separator = name.find('|')
        items = []
        if separator != -1:
            items = link.split('|')
            link = items[0]
            # If the last item contains '=', it's not a caption
            if items[-1].find('=') == -1:
                caption = items[-1]
                items = items[1:-1]
            else:
                caption = link
                items = items[1:]

        # parse the relevant items
        params = self._buildImageParams(items)
        img_path = self._getImagePath(link)

        template = jingo.env.get_template('wikiparser/hook_image.html')
        r_kwargs = {'img_path': img_path, 'caption': caption, 'params': params}
        return template.render(**r_kwargs)
