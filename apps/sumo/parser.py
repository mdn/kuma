from django.conf import settings
from django.utils.http import urlquote

from wikimarkup.parser import Parser
import jingo

from sumo.urlresolvers import reverse
from wiki.models import Document


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


def wiki_to_html(wiki_markup):
    """Wiki Markup -> HTML"""
    return WikiParser().parse(wiki_markup, show_toc=False)


def _getWikiLink(link):
    """
    Checks the page exists, and returns its URL, or the URL to create it.
    """
    try:
        d = Document.objects.get(title=link, is_template=False)
    except Document.DoesNotExist:
        # To avoid circular imports, wiki.models imports wiki_to_html
        from sumo.helpers import urlparams
        return urlparams(reverse('wiki.new_document'), title=link)
    return d.get_absolute_url()


def _hook_internal_link(parser, space, name):
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

    link = _getWikiLink(link)
    return u'<a href="%s%s">%s</a>' % (link, hash, text)


def _getImagePath(link):
    """Returns an uploaded image's path for image paths in markup."""
    return settings.WIKI_UPLOAD_URL + urlquote(link)


def _buildImageParams(items):
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
        params['link'] = _getWikiLink(params['page'])

    # Validate params with limited # of values
    for param_allowed in IMAGE_PARAMS:
        if (param_allowed in params and
            not (params[param_allowed] in IMAGE_PARAMS[param_allowed])):
            del params[param_allowed]

    return params


def _hook_image_tag(parser, space, name):
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
    params = _buildImageParams(items)
    img_path = _getImagePath(link)

    template = jingo.env.get_template('wikiparser/hook_image.html')
    r_kwargs = {'img_path': img_path, 'caption': caption, 'params': params}
    return template.render(**r_kwargs)


class WikiParser(Parser):
    """Wrapper for wikimarkup which adds Kitsune-specific callbacks and setup.
    """

    def __init__(self, base_url=None):
        super(WikiParser, self).__init__(base_url)

        # Register default hooks
        self.registerInternalLinkHook(None, _hook_internal_link)
        self.registerInternalLinkHook('Image', _hook_image_tag)

    def parse(self, text, show_toc=None, tags=None, attributes=None):
        """Given wiki markup, return HTML."""
        parser_kwargs = {'tags': tags} if tags else {}
        return super(WikiParser, self).parse(text, show_toc=show_toc,
            attributes=attributes or ALLOWED_ATTRIBUTES, **parser_kwargs)
