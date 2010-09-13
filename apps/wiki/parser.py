from HTMLParser import HTMLParser
from itertools import count
import re
from xml.sax.saxutils import quoteattr

from lxml.etree import Element, SubElement, tostring
from tower import ugettext_lazy as _lazy

import sumo.parser
from sumo.parser import ALLOWED_ATTRIBUTES


BLOCK_LEVEL_ELEMENTS = ['table', 'blockquote', 'h1', 'h2', 'h3', 'h4', 'h5',
                        'h6', 'td', 'th', 'div', 'hr', 'pre', 'p', 'li', 'ul',
                        'ol', 'center']  # from Parser.doBlockLevels

TEMPLATE_ARG_REGEX = re.compile('{{{([^{]+?)}}}')


def wiki_to_html(wiki_markup):
    """Wiki Markup -> HTML with the wiki app's enhanced parser"""
    return WikiParser().parse(wiki_markup, show_toc=False)


def _hook_include(parser, space, title):
    """Returns the document's parsed content."""
    from wiki.models import Document
    try:
        return Document.objects.get(title=title).content_parsed
    except Document.DoesNotExist:
        return _lazy('The document "%s" does not exist.') % title


# Wiki templates are documents that receive arguments.
#
# They can be useful when including similar content in multiple places,
# with slight variations. For examples and details see:
# http://www.mediawiki.org/wiki/Help:Templates
#
def _hook_template(parser, space, title):
    """Handles Template:Template name, formatting the content using given
    args"""
    from wiki.models import Document
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


class ForParser(HTMLParser):
    """Lightweight HTML parser which finds <for> tags and translates them
    into spans and divs having the proper data- elements and classes.

    As a side effect, repairs poorly matched pairings of <for> in favor of the
    location of the opening tag. Since markup comes well-formed out of the
    WikiParser, we can assume that everything is properly balanced except for
    <for> tags.

    """
    # libxml2dom balances tags the same way, but it doesn't look maintained
    # anymore, and we'd still have to parse the doc again to decide on spans
    # vs. divs.

    def __init__(self, html=''):
        """Create a parse tree from the given HTML."""
        HTMLParser.__init__(self)  # HTMLParser is an old-style class.

        self._root = Element('root')  # dummy root element to avoid branches
        self._node = self._root  # where the parser currently is in the tree

        if html:
            self.feed(html)
            self.close()

    def _make_descendent(self, tag, attrs):
        n = SubElement(self._node, tag)
        for k, v in attrs:
            n.set(k, v)
        return n

    def handle_starttag(self, tag, attrs):
        self._node = self._make_descendent(tag, attrs)

    def handle_endtag(self, tag):
        """Correct the closing of <for> tags.

        Every other kind of tag is known to be correct, since it was emitted
        from the WikiParser (which produces valid markup) and then, if that
        weren't enough, run through Bleach.

        """
        # If there's nothing on the tag stack, bail out; we discard closers
        # whose openers don't seem to be around:
        if self._node is self._root:
            return

        while self._node.tag != tag and self._node.tag == 'for':
            # Somebody closed one or more <for>s late: <em><for>We are
            # here: ^</em>. Close them. Don't force-close non-for tags.
            # They are known to be right; </for> placement is at fault.
            self._node = self._node.getparent()
            if self._node is self._root:
                return

        # Close the tag we actually encountered if it's the one we expect.
        # Either self._node matches the closer we're at, or self._node isn't a
        # <for>. The latter case indicates that the input stream is at fault,
        # in which case we ignore the closer.
        if self._node.tag == tag:
            self._node = self._node.getparent()

    def handle_startendtag(self, tag, attrs):
        """Slam down a new tag, but don't move the node pointer."""
        self._make_descendent(tag, attrs)

    def handle_data(self, data):
        # How I hate lxml's choice of not making text nodes proper nodes.
        n = self._node
        if len(n):  # Even some childless nodes are True.
            if n[-1].tail:
                n[-1].tail += data
            else:
                n[-1].tail = data
        else:
            if n.text:
                n.text += data
            else:
                n.text = data

    def expand_fors(self):
        """Turn the for tags into spans and divs, and apply data attrs.

        If a for contains any block-level elements, it turns into a div.
        Otherwise, it turns into a span.

        """
        for for_el in self._root.xpath('//for'):
            for_el.tag = ('div' if any(for_el.find(tag) is not None
                                        for tag in BLOCK_LEVEL_ELEMENTS)
                                 else 'span')
            for_el.attrib['class'] = 'for'

    def to_unicode(self):
        """Return the unicode serialization of myself."""
        r = len('<root>')
        return tostring(self._root, encoding=unicode)[r:-r - 1]

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
                    prespace += paragraph_padding(prespace)

                # If tag (including trailing whitespace) wasn't at the bottom
                # of the document, space it off from following block elements:
                if not at_bottom:
                    postspace += paragraph_padding(postspace)

            return prespace + token + postspace

        return cls._FOR_OR_CLOSER.sub(dehydrate, text), dehydrations

    # Dratted wiki formatter likes to put <p> tags around my token when it sits
    # on a line by itself, so tolerate and consume that foolishness:
    _PARSED_STRIPPED_FOR = re.compile(r'<p>\s*\x07(\d+)\x07\s*</p>'
                                          r'|\x07(\d+)\x07')
    _PARSED_STRIPPED_FOR_CLOSER = re.compile(r'<p>\s*\x07/sf\x07\s*</p>'
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


class WikiParser(sumo.parser.WikiParser):
    """An extension of the parser from the forums adding more crazy features

    {for} tags, inclusions, and templates--oh my!

    """
    def __init__(self, base_url=None):
        super(WikiParser, self).__init__(base_url)

        # The wiki has additional hooks not used elsewhere
        self.registerInternalLinkHook('Include', _hook_include)
        self.registerInternalLinkHook('Template', _hook_template)
        self.registerInternalLinkHook('T', _hook_template)

    def parse(self, text, **kwargs):
        """Wrap SUMO's parse() to support additional wiki-only features."""
        # Do simple substitutions:
        text = parse_simple_syntax(text)

        # Replace fors with inline tokens the wiki formatter will tolerate:
        text, data = ForParser.strip_fors(text)

        # Run the formatter:
        html = super(WikiParser, self).parse(text, **kwargs)

        # Put the fors back in (as XML-ish <for> tags this time):
        html = ForParser.unstrip_fors(html, data)

        # Balance badly paired <for> tags:
        for_parser = ForParser(html)

        # Convert them to spans and divs:
        for_parser.expand_fors()

        return for_parser.to_unicode()
