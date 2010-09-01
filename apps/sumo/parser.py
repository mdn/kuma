import re

from django.conf import settings
from django.utils.http import urlquote

from wikimarkup.parser import Parser
import jingo
from tower import ugettext_lazy as _lazy

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

TEMPLATE_ARG_REGEX = re.compile('{{{([^{]+?)}}}')


class WikiParser(Parser):
    """Wrapper for wikimarkup which adds Kitsune-specific callbacks and setup.
    """

    def __init__(self, base_url=None, wiki_hooks=False):
        super(WikiParser, self).__init__(base_url)

        # Register default hooks
        self.registerInternalLinkHook(None, _hook_internal_link)
        self.registerInternalLinkHook('Image', _hook_image_tag)

        # The wiki has additional hooks not used elsewhere
        if wiki_hooks:
            self.registerInternalLinkHook('Include', _hook_include)
            self.registerInternalLinkHook('Template', _hook_template)
            self.registerInternalLinkHook('T', _hook_template)

    def parse(self, text, show_toc=True, tags=None, attributes=None):
        """Given wiki markup, return HTML."""
        text = parse_simple_syntax(text)
        parser_kwargs = {'tags': tags} if tags else {}
        return super(WikiParser, self).parse(text, show_toc=show_toc, attributes=attributes or ALLOWED_ATTRIBUTES, **parser_kwargs)


# Wiki parser hooks

def _hook_include(parser, space, title):
    """Returns the document's parsed content."""
    from wiki.models import Document
    try:
        return Document.objects.get(title=title).content_parsed
    except Document.DoesNotExist:
        return _lazy('The document "%s" does not exist.') % title


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


# Wiki templates are documents that receive arguments.
#
# They can be useful when including similar content in multiple places,
# with slight variations. For examples and details see:
# http://www.mediawiki.org/wiki/Help:Templates
#
def _hook_template(parser, space, title):
    """Handles Template:Template name, formatting the content using given
    args"""
    # To avoid circular imports, wiki.models imports wiki_to_html
    params = title.split('|')
    short_title = params.pop(0)
    template_title = 'Template:' + short_title

    try:
        t = Document.objects.get(title=template_title, is_template=True)
    except Document.DoesNotExist:
        return _lazy('The template "%s" does not exist.') % short_title

    c = t.current_revision.content.rstrip()
    # Note: this completely ignores the allowed attributes passed to the
    # WikiParser.parse() method, and defaults to ALLOWED_ATTRIBUTES
    parsed = parser.parse(c, show_toc=False, attributes=ALLOWED_ATTRIBUTES)

    if '\n' not in c:
        parsed = parsed.replace('<p>', '')
        parsed = parsed.replace('</p>', '')
    # Do some string formatting to replace parameters
    return _format_template_content(parsed, _build_template_params(params))


def _format_template_content(content, params):
    """Formats a template's content using passed in arguments"""

    def arg_replace(matchobj):
        """Takes a regex matching {{{name}} and returns params['name']"""
        param_name = matchobj.group(1)
        if param_name in params:
            return params[param_name]

    return TEMPLATE_ARG_REGEX.sub(arg_replace, content)


def _build_template_params(params_str):
    """Builds a dictionary from a given list of raw strings passed in by the
    user.

    Example syntax it handles:
    * ['one', 'two']   turns into     {1: 'one', 2: 'two'}
    * ['12=blah']      turns into     {12: 'blah'}
    * ['name=value']   turns into     {'name': 'value'}

    """
    i = 0
    params = {}
    for item in params_str:
        param, _, value = item.partition('=')

        if value:
            params[param] = value
        else:
            i = i + 1
            params[str(i)] = param

    return params


# Custom syntax using regexes follows below.
# * turn tags of the form {tag content} into <span class="tag">content</span>
# * expand {key ctrl+alt} into <span class="key">ctrl</span> +
#   <span class="key">alt</span>
# * turn {note}note{/note} into <div class="note">a note</div>

def _key_split(matchobj):
    """Expands a {key a+b+c} syntax into <span class="key">a</span> + ...

    More explicitly, it takes a regex matching {key ctrl+alt+del} and returns:
    <span class="key">ctrl</span> + <span class="key">alt</span> +
    <span class="key">del</span>

    """
    keys = [k.strip() for k in matchobj.group(1).split('+')]
    return ' + '.join(['<span class="key">%s</span>' % key for key in keys])


PATTERNS = [
    (re.compile(pattern, re.DOTALL), replacement) for
    pattern, replacement in (
        # (x, y), replace x with y
        (r'{(?P<name>note|warning)}', '<div class="\g<name>">'),
        (r'\{/(note|warning)\}', '</div>'),
        # To use } as a key, this syntax won't work. Use [[T:key|}]] instead
        (r'\{key (.+?)\}', _key_split),  # ungreedy: stop at the first }
        (r'{(?P<name>button|menu|filepath) (?P<content>.*?)}',
         '<span class="\g<name>">\g<content></span>'),
    )]


def parse_simple_syntax(text):
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text
