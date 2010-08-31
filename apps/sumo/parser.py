from django.conf import settings
from django.utils.http import urlquote
from django.conf import settings

from wikimarkup.parser import Parser
import jingo
from tower import ugettext_lazy as _lazy

from sumo.urlresolvers import reverse
from .models import WikiPage


ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'class', 'rel'],
    'div': ['id', 'class', 'style'],
    'h1': ['id'],
    'h2': ['id'],
    'h3': ['id'],
    'h4': ['id'],
    'h5': ['id'],
    'h6': ['id'],
    'li': ['class'],
    'span': ['class'],
    'img': ['class', 'src', 'alt', 'title', 'height', 'width', 'style'],
}


IMAGE_PARAMS = {
    'align': ('none', 'left', 'center', 'right'),
    'valign': ('baseline', 'sub', 'super', 'top', 'text-top', 'middle',
              'bottom', 'text-bottom'),
}


class WikiParser(object):
    """
    Wrapper for wikimarkup. Adds Kitsune-specific callbacks and setup.
    """

    def __init__(self, wiki_hooks=False):
        self.parser = Parser()
        # Register default hooks
        self.parser.registerInternalLinkHook(None, self.hook_internal_link)
        self.parser.registerInternalLinkHook('Image', self.hook_image_tag)

        # The wiki has additional hooks not used elsewhere
        if wiki_hooks:
            self.parser.registerInternalLinkHook('Include', self.hook_include)

    def parse(self, text, showToc=True):
        """Given wiki markup, return HTML."""
        return self.parser.parse(text, showToc, attributes=ALLOWED_ATTRIBUTES)

    def hook_include(self, parser, space, title):
        """Returns the document's parsed content."""
        from wiki.models import Document
        try:
            return Document.objects.get(title=title).content_parsed
        except Document.DoesNotExist:
            return _lazy('The document "%s" does not exist.') % title

    def _getWikiLink(self, link):
        """
        Checks the page exists, and returns its URL, or the URL to create it.
        """
        return reverse('wiki.document',
                       kwargs={'document_slug': link.replace(' ', '+')})

    def hook_internal_link(self, parser, space, name):
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
        return settings.WIKI_UPLOAD_URL + urlquote(link)

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
                params[item] = True

        if 'page' in params and params['page'] is not True:
            params['link'] = self._getWikiLink(params['page'])

        # Validate params with limited # of values
        for param_allowed in IMAGE_PARAMS:
            if (param_allowed in params and
                not (params[param_allowed] in IMAGE_PARAMS[param_allowed])):
                del params[param_allowed]

        return params

    def hook_image_tag(self, parser, space, name):
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
