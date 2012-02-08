from itertools import count
from os.path import basename
import re
from xml.sax.saxutils import quoteattr

from django.conf import settings

from html5lib import HTMLParser
from html5lib.serializer.htmlserializer import HTMLSerializer
from html5lib.treebuilders import getTreeBuilder
from html5lib.treewalkers import getTreeWalker
import jingo
from lxml.etree import Element

from tower import ugettext as _, ugettext_lazy as _lazy

from gallery.models import Video
import sumo.parser
from sumo.parser import get_object_fallback, build_hook_params


BLOCK_LEVEL_ELEMENTS = ['table', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5',
                        'h6', 'td', 'th', 'div', 'hr', 'pre', 'p', 'li', 'ul',
                        'ol', 'center', 'dl', 'dt', 'dd', 'ins', 'del',
                        'section']  # block elements wikimarkup
                                    # knows about (and thus preserves)
VIDEO_PARAMS = ['height', 'width', 'modal', 'title', 'placeholder']
TEMPLATE_ARG_REGEX = re.compile('{{{([^{]+?)}}}')


def wiki_to_html(wiki_markup, locale=settings.WIKI_DEFAULT_LANGUAGE,
                 doc_id=None):
    """Wiki Markup -> HTML with the wiki app's enhanced parser"""
    return WikiParser(doc_id=doc_id).parse(wiki_markup, show_toc=False,
                                           locale=locale)


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
        param, __, value = item.partition('=')
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
        (r'{(?P<name>button|menu|filepath|pref) (?P<content>.*?)}',
         '<span class="\g<name>">\g<content></span>'),
    )]


def parse_simple_syntax(text):
    for pattern, replacement in PATTERNS:
        text = pattern.sub(replacement, text)
    return text


class ForParser(object):
    """HTML 5 parser which finds <for> tags and translates them into spans and
    divs having the proper data- elements and classes.

    As a side effect, repairs poorly matched pairings of <for> (and other
    tags), probably in favor of the location of the opening tag.

    """
    TREEBUILDER = 'lxml'
    CONTAINER_TAG = 'div'

    def __init__(self, html):
        """Create a parse tree from the given HTML."""
        def really_parse_fragment(parser, html):
            """Parse a possibly multi-rooted HTML fragment, wrapping it in a
            <div> to make it easy to query later.

            As far as I can tell, this is what parseFragment is supposed to do
            (but doesn't). See
            http://code.google.com/p/html5lib/issues/detail?id=161.

            """
            top_level_elements = parser.parseFragment(html)
            container = Element(self.CONTAINER_TAG)

            # Why lxml couldn't just have text nodes, I'll never understand.
            # Text nodes that come other than first are automatically stuffed
            # into the tail attrs of the preceding elements by html5lib.
            if top_level_elements and isinstance(top_level_elements[0],
                                                 basestring):
                container.text = top_level_elements.pop(0)

            container.extend(top_level_elements)
            return container

        p = HTMLParser(tree=getTreeBuilder(self.TREEBUILDER))
        self._root = really_parse_fragment(p, html)

    def expand_fors(self):
        """Turn the for tags into spans and divs, and apply data attrs.

        If a for contains any block-level elements, it turns into a div.
        Otherwise, it turns into a span.

        """
        html_ns = 'http://www.w3.org/1999/xhtml'
        for for_el in self._root.xpath('//html:for',
                                       namespaces={'html': html_ns}):
            for_el.tag = ('div' if any(for_el.find('{' + html_ns + '}' + tag)
                                       is not None
                                       for tag in BLOCK_LEVEL_ELEMENTS)
                                 else 'span')
            for_el.attrib['class'] = 'for'

    def to_unicode(self):
        """Return the unicode serialization of myself."""
        container_len = len(self.CONTAINER_TAG) + 2  # 2 for the <>
        walker = getTreeWalker(self.TREEBUILDER)
        stream = walker(self._root)
        serializer = HTMLSerializer(quote_attr_values=True,
                                    omit_optional_tags=False)
        return serializer.render(stream)[container_len:-container_len - 1]

    @staticmethod
    def _on_own_line(match, postspace):
        """Return (whether the tag is on its own line, whether the tag is at
        the very top of the string, whether the tag is at the very bottom of
        the string).

        Tolerates whitespace to the right of the tag: a tag with trailing
        whitespace on the line can still be considered to be on its own line.

        """
        pos_before_tag = match.start(2) - 1
        if pos_before_tag >= 0:
            at_left = match.string[pos_before_tag] == '\n'
            at_top = False
        else:
            at_left = at_top = True
        at_bottom_modulo_space = match.end(4) == len(match.string)
        at_right_modulo_space = at_bottom_modulo_space or '\n' in postspace
        return (at_left and at_right_modulo_space,
                at_top, at_bottom_modulo_space)

    @staticmethod
    def _wiki_to_tag(attrs):
        """Turn {for ...} into <for data-for="...">."""
        if not attrs:
            return '<for>'
        # Strip leading and trailing whitespace from each value for easier
        # matching in the JS:
        stripped = ','.join([x.strip() for x in attrs.split(',')])
        return '<for data-for=' + quoteattr(stripped) + '>'

    _FOR_OR_CLOSER = re.compile(r'(\s*)'
                                r'(\{for(?: +([^\}]*))?\}|{/for})'
                                r'(\s*)', re.MULTILINE)

    @classmethod
    def strip_fors(cls, text):
        """Replace each {for} or {/for} tag with a unique token the
        wiki formatter will treat as inline.

        Return (stripped text,
                dehydrated fors for use with unstrip_fors).

        """
        # Replace {for ...} tags:
        dehydrations = {}  # "attributes" of {for a, b} directives, like
                           # "a, b", keyed by token number
        indexes = count()

        def dehydrate(match):
            """Close over `dehydrations`, sock the {for}s away therein, and
            replace {for}s and {/for}s with tokens."""
            def paragraph_padding(str):
                """If str doesn't contain at least 2 newlines, return enough
                such that appending them will cause it to."""
                return '\n' * max(2 - str.count('\n'), 0)

            def preceding_whitespace(str, pos):
                """Return all contiguous whitespace preceding str[pos]."""
                whitespace = []
                for i in xrange(pos - 1, 0, -1):
                    if str[i] in '\t \n\r':
                        whitespace.append(str[i])
                    else:
                        break
                whitespace.reverse()
                return ''.join(whitespace)

            prespace, tag, attrs, postspace = match.groups()

            if tag != '{/for}':
                i = indexes.next()
                dehydrations[i] = cls._wiki_to_tag(attrs)
                token = u'\x07%i\x07' % i
            else:
                token = u'\x07/sf\x07'

            # If the {for} or {/for} is on a line by itself (righthand
            # whitespace is allowed; left would indicate a <pre>), make sure it
            # has enough newlines on each side to make it its own paragraph,
            # lest it get sucked into being part of the next or previous
            # paragraph:
            on_own_line, at_top, at_bottom = cls._on_own_line(match, postspace)
            if on_own_line:
                # If tag (excluding leading whitespace) wasn't at top of
                # document, space it off from preceding block elements:
                if not at_top:
                    # If there are already enough \ns before the tag to
                    # distance it from the preceding paragraph, take them into
                    # account before adding more.
                    prespace += paragraph_padding(
                                    preceding_whitespace(match.string,
                                                         match.start(1))
                                    + prespace)

                # If tag (including trailing whitespace) wasn't at the bottom
                # of the document, space it off from following block elements:
                if not at_bottom:
                    postspace += paragraph_padding(postspace)

            return prespace + token + postspace

        # Do single replaces over and over, taking into account the effects of
        # previous ones so that whitespace added in a previous replacement can
        # be considered for its role in helping to nudge an adjacent block-
        # level {for} into its own paragraph. There's no pos arg to replace(),
        # so we had to write our own.
        pos = 0
        while True:
            m = cls._FOR_OR_CLOSER.search(text, pos)
            if m is None:
                return text, dehydrations
            done = text[:m.start()] + dehydrate(m)  # already been searched
            pos = len(done)
            text = done + text[m.end():]

    # Dratted wiki formatter likes to put <p> tags around my token when it sits
    # on a line by itself, so tolerate and consume that foolishness:
    _PARSED_STRIPPED_FOR = re.compile(
        # Whitespace, a {for} token, then more whitespace (including <br>s):
        r'<p>'
        r'(?:\s|<br\s*/?>)*'
        r'\x07(\d+)\x07'  # The {for} token
        r'(?:\s|<br\s*/?>)*'
        r'</p>'
        # Alternately, a lone {for} token that didn't get wrapped in a <p>:
        r'|\x07(\d+)\x07')
    _PARSED_STRIPPED_FOR_CLOSER = re.compile(
        # Similar to above, a {/for} token wrapped in <p> and whitespace:
        r'<p>'
        r'(?:\s|<br\s*/?>)*'
        r'\x07/sf\x07'  # {/for} token
        r'(?:\s|<br\s*/?>)*'
        r'</p>'
        # Or a lone {/for} token:
        r'|\x07/sf\x07')

    @classmethod
    def unstrip_fors(cls, html, dehydrations):
        """Replace the tokens with <for> tags the ForParser understands."""
        def hydrate(match):
            return dehydrations.get(int(match.group(1) or match.group(2)), '')

        # Put <for ...> tags back in:
        html = cls._PARSED_STRIPPED_FOR.sub(hydrate, html)

        # Replace {/for} tags:
        return cls._PARSED_STRIPPED_FOR_CLOSER.sub(u'</for>', html)


# L10n: This error is displayed if a template is included into itself.
RECURSION_MESSAGE = _lazy(u'[Recursive inclusion of "%s"]')


class WikiParser(sumo.parser.WikiParser):
    """An extension of the parser from the forums adding more crazy features

    {for} tags, inclusions, and templates--oh my!

    """
    def __init__(self, base_url=None, doc_id=None):
        """
        doc_id -- If you want to be nice, pass the ID of the Document you are
            rendering. This will make recursive inclusions fail immediately
            rather than after the first round of recursion.

        """
        super(WikiParser, self).__init__(base_url)

        # Stack of document IDs to prevent Include or Template recursion:
        self.inclusions = [doc_id] if doc_id else []

        # The wiki has additional hooks not used elsewhere
        self.registerInternalLinkHook('Include', self._hook_include)
        self.registerInternalLinkHook('I', self._hook_include)
        self.registerInternalLinkHook('Template', self._hook_template)
        self.registerInternalLinkHook('T', self._hook_template)
        self.registerInternalLinkHook('Video', self._hook_video)
        self.registerInternalLinkHook('V', self._hook_video)

    def parse(self, text, **kwargs):
        """Wrap SUMO's parse() to support additional wiki-only features."""
        # Replace fors with inline tokens the wiki formatter will tolerate:
        text, data = ForParser.strip_fors(text)

        # Do simple substitutions:
        text = parse_simple_syntax(text)

        # Run the formatter:
        html = super(WikiParser, self).parse(text, **kwargs)

        # Put the fors back in (as XML-ish <for> tags this time):
        html = ForParser.unstrip_fors(html, data)

        # Balance badly paired <for> tags:
        for_parser = ForParser(html)

        # Convert them to spans and divs:
        for_parser.expand_fors()

        return for_parser.to_unicode()

    def _hook_include(self, parser, space, title):
        """Returns the document's parsed content."""
        from wiki.models import Document
        message = _('The document "%s" does not exist.') % title
        t = get_object_fallback(Document, title, locale=self.locale)
        if not t or not t.current_revision:
            return message

        if t.id in parser.inclusions:
            return RECURSION_MESSAGE % title
        else:
            parser.inclusions.append(t.id)
        ret = parser.parse(t.current_revision.content, show_toc=False,
                           locale=self.locale)
        parser.inclusions.pop()
        return ret

    # Wiki templates are documents that receive arguments.
    #
    # They can be useful when including similar content in multiple places,
    # with slight variations. For examples and details see:
    # http://www.mediawiki.org/wiki/Help:Templates
    #
    def _hook_template(self, parser, space, title):
        """Handles Template:Template name, formatting the content using given
        args"""
        from wiki.models import Document
        from wiki.models import ALLOWED_ATTRIBUTES
        params = title.split('|')
        short_title = params.pop(0)
        template_title = 'Template:' + short_title

        message = _('The template "%s" does not exist or has no approved '
                    'revision.') % short_title
        t = get_object_fallback(Document, template_title,
                                locale=self.locale, is_template=True)

        if not t or not t.current_revision:
            return message

        if t.id in parser.inclusions:
            return RECURSION_MESSAGE % template_title
        else:
            parser.inclusions.append(t.id)
        c = t.current_revision.content.rstrip()
        # Note: this completely ignores the allowed attributes passed to the
        # WikiParser.parse() method and defaults to ALLOWED_ATTRIBUTES.
        parsed = parser.parse(c, show_toc=False, attributes=ALLOWED_ATTRIBUTES,
                              locale=self.locale)
        parser.inclusions.pop()

        # Special case for inline templates
        if '\n' not in c:
            parsed = parsed.replace('<p>', '')
            parsed = parsed.replace('</p>', '')
        # Do some string formatting to replace parameters
        return _format_template_content(parsed, _build_template_params(params))

    # Videos are objects that can have one or more files attached to them
    #
    # They are keyed by title in the syntax and the locale passed to the
    # parser.
    def _hook_video(self, parser, space, title):
        """Handles [[Video:video title]] with locale from parser."""
        message = _lazy(u'The video "%s" does not exist.') % title

        # params, only modal supported for now
        title, params = build_hook_params(title, self.locale, VIDEO_PARAMS)

        v = get_object_fallback(Video, title, self.locale, message)
        if isinstance(v, basestring):
            return v

        return generate_video(v, params)


def generate_video(v, params=[]):
    """Takes a video object and returns HTML markup for embedding it."""
    sources = []
    if v.webm:
        sources.append({'src': _get_video_url(v.webm), 'type': 'webm'})
    if v.ogv:
        sources.append({'src': _get_video_url(v.ogv), 'type': 'ogg'})
    data_fallback = ''
    # Flash fallback
    if v.flv:
        data_fallback = _get_video_url(v.flv)
    return jingo.env.get_template('wikiparser/hook_video.html').render(
        {'fallback': data_fallback, 'sources': sources, 'params': params,
         'video': v,
         'height': settings.WIKI_VIDEO_HEIGHT,
         'width': settings.WIKI_VIDEO_WIDTH})


def _get_video_url(video_file):
    if settings.GALLERY_VIDEO_URL:
        return settings.GALLERY_VIDEO_URL + basename(video_file.name)
    return video_file.url
