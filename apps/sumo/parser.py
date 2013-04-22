from django.conf import settings

import jingo
from tower import ugettext_lazy as _lazy
from wikimarkup.parser import Parser

from sumo.urlresolvers import reverse
from wiki.models import Document


ALLOWED_ATTRIBUTES = {
    'a': ['href', 'title', 'class', 'rel'],
    'div': ['id', 'class', 'style', 'data-for', 'title', 'data-target',
            'data-modal'],
    'h1': ['id'],
    'h2': ['id'],
    'h3': ['id'],
    'h4': ['id'],
    'h5': ['id'],
    'h6': ['id'],
    'li': ['class'],
    'span': ['class', 'data-for'],
    'img': ['class', 'src', 'alt', 'title', 'height', 'width', 'style'],
    'video': ['height', 'width', 'controls', 'data-fallback', 'poster'],
    'source': ['src', 'type'],
}
IMAGE_PARAMS = ['alt', 'align', 'caption', 'valign', 'frame', 'page', 'link',
                'width', 'height']
IMAGE_PARAM_VALUES = {
    'align': ('none', 'left', 'center', 'right'),
    'valign': ('baseline', 'sub', 'super', 'top', 'text-top', 'middle',
              'bottom', 'text-bottom'),
}


def wiki_to_html(wiki_markup, locale=settings.WIKI_DEFAULT_LANGUAGE):
    """Wiki Markup -> HTML"""
    return WikiParser().parse(wiki_markup, show_toc=False, locale=locale)


def get_object_fallback(cls, title, locale, default=None, **kwargs):
    """Return an instance of cls matching title and locale, or fall back to the
    default locale.

    When falling back to the default locale, follow any wiki redirects
    internally.

    If the fallback fails, the return value is `default`.

    You may pass in additional kwargs which go straight to the query.

    """
    try:
        return cls.objects.get(title=title, locale=locale, **kwargs)
    except cls.DoesNotExist:
        pass

    # Fallback
    try:
        default_lang_doc = cls.objects.get(
            title=title, locale=settings.WIKI_DEFAULT_LANGUAGE, **kwargs)

        # Return the translation of this English item:
        if hasattr(default_lang_doc, 'translated_to'):
            trans = default_lang_doc.translated_to(locale)
            if trans and trans.current_revision:
                return trans

        # Follow redirects internally in an attempt to find a translation of
        # the final redirect target in the requested locale. This happens a lot
        # when an English article is renamed and a redirect is left in its
        # wake: we wouldn't want the non-English user to be linked to the
        # English redirect, which would happily redirect them to the English
        # final article.
        if hasattr(default_lang_doc, 'redirect_document'):
            target = default_lang_doc.redirect_document()
            if target:
                trans = target.translated_to(locale)
                if trans and trans.current_revision:
                    return trans

        # Return the English item:
        return default_lang_doc
    # Okay, all else failed
    except cls.DoesNotExist:
        return default


def _get_wiki_link(title, locale):
    """Checks the page exists, and returns its URL or the URL to create it.

    Return value is a dict: {'found': boolean, 'url': string}.
    found is False if the document does not exist.

    """
    d = get_object_fallback(Document, locale=locale, title=title,
                            is_template=False)
    if d:
        return {'found': True, 'url': d.get_absolute_url(), 'text': d.title}

    # To avoid circular imports, wiki.models imports wiki_to_html
    from sumo.helpers import urlparams
    return {'found': False,
            'text': title,
            'url': urlparams(reverse('wiki.new_document', locale=locale),
                             title=title)}


def build_hook_params(string, locale, allowed_params=[],
                      allowed_param_values={}):
    """Parses a string of the form 'some-title|opt1|opt2=arg2|opt3...'

    Builds a list of items and returns relevant parameters in a dict.

    """
    if not '|' in string:  # No params? Simple and easy.
        string = string.strip()
        return (string, {'alt': string})

    items = [i.strip() for i in string.split('|')]
    title = items.pop(0)
    params = {}

    last_item = ''
    for item in items:  # this splits by = or assigns the dict key to True
        if '=' in item:
            param, value = item.split('=', 1)
            params[param] = value
        else:
            params[item] = True
            last_item = item

    if 'caption' in allowed_params:
        params['caption'] = title
        # Allowed parameters are not caption. All else is.
        if last_item and last_item not in allowed_params:
            params['caption'] = items.pop()
            del params[last_item]
        elif last_item == 'caption':
            params['caption'] = last_item

    # Validate params allowed
    for p in params.keys():
        if p not in allowed_params:
            del params[p]

    # Validate params with limited # of values
    for p in allowed_param_values:
        if p in params and params[p] not in allowed_param_values[p]:
            del params[p]

    # Handle page as a special case
    if 'page' in params and params['page'] is not True:
        link = _get_wiki_link(params['page'], locale)
        params['link'] = link['url']
        params['found'] = link['found']

    return (title, params)


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
        text = False
        title = name

        # Split on pipe -- [[href|name]]
        if '|' in name:
            title, text = title.split('|', 1)

        hash = ''
        if '#' in title:
            title, hash = title.split('#', 1)

        # Sections use _, page names use +
        if hash != '':
            hash = '#' + hash.replace(' ', '_')

        # Links to this page can just contain href="#hash"
        if title == '' and hash != '':
            if not text:
                text = hash.replace('_', ' ')
            return u'<a href="%s">%s</a>' % (hash, text)

        link = _get_wiki_link(title, self.locale)
        a_cls = ''
        if not link['found']:
            a_cls = ' class="new"'
        if not text:
            text = link['text']
        return u'<a href="%s%s"%s>%s</a>' % (link['url'], hash, a_cls, text)

    def _hook_image_tag(self, parser, space, name):
        """Adds syntax for inserting images."""
        title, params = build_hook_params(name, self.locale, IMAGE_PARAMS,
                                          IMAGE_PARAM_VALUES)

        message = _lazy(u'The image "%s" does not exist.') % title
        image = get_object_fallback(Image, title, self.locale, message)
        if isinstance(image, basestring):
            return image

        template = jingo.env.get_template('wikiparser/hook_image.html')
        r_kwargs = {'image': image, 'params': params}
        return template.render(**r_kwargs)
