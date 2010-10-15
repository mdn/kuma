from django.conf import settings

import jingo
from tower import ugettext_lazy as _lazy
from wikimarkup.parser import Parser

from gallery.models import Image
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
    'video': ['height', 'width', 'controls', 'data-fallback'],
    'source': ['src', 'type'],
}
IMAGE_PARAMS = {
    'align': ('none', 'left', 'center', 'right'),
    'valign': ('baseline', 'sub', 'super', 'top', 'text-top', 'middle',
              'bottom', 'text-bottom'),
}


def wiki_to_html(wiki_markup, locale=settings.WIKI_DEFAULT_LANGUAGE):
    """Wiki Markup -> HTML"""
    return WikiParser().parse(wiki_markup, show_toc=False, locale=locale)


def get_object_fallback(cls, title, locale, default=None, **kwargs):
    """Returns an instance of cls matching title, locale, or falls back.

    If the fallback fails, the return value is default.
    You may pass in additional kwargs which go straight to the query.

    """
    try:
        return cls.objects.get(title=title, locale=locale, **kwargs)
    except cls.DoesNotExist:
        pass

    # Fallback
    try:
        return cls.objects.get(
            title=title, locale=settings.WIKI_DEFAULT_LANGUAGE, **kwargs)
    # Okay, all else failed
    except cls.DoesNotExist:
        return default


def _getWikiLink(link, locale):
    """Checks the page exists, and returns its URL or the URL to create it."""
    try:
        d = Document.objects.get(locale=locale, title=link, is_template=False)
    except Document.DoesNotExist:
        # To avoid circular imports, wiki.models imports wiki_to_html
        from sumo.helpers import urlparams
        return urlparams(reverse('wiki.new_document'), title=link)
    return d.get_absolute_url()


def _buildImageParams(items, locale):
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
        params['link'] = _getWikiLink(params['page'], locale)

    # Validate params with limited # of values
    for param_allowed in IMAGE_PARAMS:
        if (param_allowed in params and
            not (params[param_allowed] in IMAGE_PARAMS[param_allowed])):
            del params[param_allowed]

    return params


class WikiParser(Parser):
    """Wrapper for wikimarkup which adds Kitsune-specific callbacks and setup.
    """

    def __init__(self, base_url=None):
        super(WikiParser, self).__init__(base_url)

        # Register default hooks
        self.registerInternalLinkHook(None, self._hook_internal_link)
        self.registerInternalLinkHook('Image', self._hook_image_tag)

    def parse(self, text, show_toc=None, tags=None, attributes=None,
              locale=settings.WIKI_DEFAULT_LANGUAGE):
        """Given wiki markup, return HTML.

        Pass a locale to get all the hooks to look up Documents or Media
        (Video, Image) for that locale. We key Documents by title and locale,
        so both are required to identify it for a e.g. link.

        Since py-wikimarkup's hooks don't offer custom paramters for callbacks,
        we're using self.locale to keep things simple."""
        self.locale = locale

        parser_kwargs = {'tags': tags} if tags else {}
        return super(WikiParser, self).parse(text, show_toc=show_toc,
            attributes=attributes or ALLOWED_ATTRIBUTES, **parser_kwargs)

    def _hook_internal_link(self, parser, space, name):
        """Parses text and returns internal link."""
        link = text = name

        # Split on pipe -- [[href|name]]
        if '|' in name:
            link, text = link.split('|', 1)

        hash = ''
        if '#' in link:
            link, hash = link.split('#', 1)

        # Sections use _, page names use +
        if hash != '':
            hash = '#' + hash.replace(' ', '_')

        # Links to this page can just contain href="#hash"
        if link == '' and hash != '':
            return u'<a href="%s">%s</a>' % (hash, text)

        link = _getWikiLink(link, self.locale)
        return u'<a href="%s%s">%s</a>' % (link, hash, text)

    def _hook_image_tag(self, parser, space, name):
        """Adds syntax for inserting images."""
        title = name
        caption = name
        params = {}

        # Parse the inner syntax, e.g. [[Image:src|option=val|caption]]
        separator = name.find('|')
        items = []
        if separator != -1:
            items = title.split('|')
            title = items[0]
            # If the last item contains '=', it's not a caption
            if items[-1].find('=') == -1:
                caption = items[-1]
                items = items[1:-1]
            else:
                caption = title
                items = items[1:]

        message = _lazy('The image "%s" does not exist.') % title
        image = get_object_fallback(Image, title, self.locale, message)
        if isinstance(image, basestring):
            return image

        # parse the relevant items
        params = _buildImageParams(items, self.locale)

        template = jingo.env.get_template('wikiparser/hook_image.html')
        r_kwargs = {'image': image, 'caption': caption, 'params': params}
        return template.render(**r_kwargs)
