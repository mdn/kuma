import logging
import re
from urllib import urlencode

from xml.sax.saxutils import quoteattr

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter
from pyquery import PyQuery as pq

from tower import ugettext as _

from sumo.urlresolvers import reverse


# Regex to extract language from MindTouch code elements' function attribute
MT_SYNTAX_PAT = re.compile(r"""syntax\.(\w+)""")
# map for mt syntax values that should turn into new brush values
MT_SYNTAX_BRUSH_MAP = {
    'javascript': 'js',
}

# List of tags supported for section editing. A subset of everything that could
# be considered an HTML5 section
SECTION_TAGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hgroup', 'section')

HEAD_TAGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6')

# Head tags to included in the table of contents
HEAD_TAGS_TOC = ('h1', 'h2', 'h3', 'h4')


def parse(src):
    return ContentSectionTool(src)


def filter_out_noinclude(src):
    """Quick and dirty filter to remove <div class="noinclude"> blocks"""
    # NOTE: This started as an html5lib filter, but it started getting really
    # complex. Seems like pyquery works well enough without corrupting
    # character encoding.
    doc = pq(src)
    doc.remove('*[class=noinclude]')
    return doc.html()


class ContentSectionTool(object):

    def __init__(self, src=None):

        self.tree = html5lib.treebuilders.getTreeBuilder("simpletree")

        self.parser = html5lib.HTMLParser(tree=self.tree,
            namespaceHTMLElements=False)

        self.serializer = html5lib.serializer.htmlserializer.HTMLSerializer(
            omit_optional_tags=False, quote_attr_values=True,
            escape_lt_in_attrs=True)

        self.walker = html5lib.treewalkers.getTreeWalker("simpletree")

        self.src = ''
        self.doc = None
        self.stream = []

        if (src):
            self.parse(src)

    def parse(self, src):
        self.src = src
        self.doc = self.parser.parseFragment(self.src)
        self.stream = self.walker(self.doc)
        return self

    def serialize(self, stream=None):
        if stream is None:
            stream = self.stream
        return u"".join(self.serializer.serialize(stream))

    def __unicode__(self):
        return self.serialize()

    def filter(self, filter_cls):
        self.stream = filter_cls(self.stream)
        return self

    def injectSectionIDs(self):
        self.stream = SectionIDFilter(self.stream)
        return self

    def injectSectionEditingLinks(self, full_path, locale):
        self.stream = SectionEditLinkFilter(self.stream, full_path, locale)
        return self

    def extractSection(self, id):
        self.stream = SectionFilter(self.stream, id)
        return self

    def replaceSection(self, id, replace_src):
        replace_stream = self.walker(self.parser.parseFragment(replace_src))
        self.stream = SectionFilter(self.stream, id, replace_stream)
        return self


class SectionIDFilter(html5lib_Filter):
    """Filter which ensures section-related elements have unique IDs"""

    def __init__(self, source):
        html5lib_Filter.__init__(self, source)
        self.id_cnt = 0
        self.known_ids = set()

    def gen_id(self):
        """Generate a unique ID"""
        while True:
            self.id_cnt += 1
            id = 'sect%s' % self.id_cnt
            if id not in self.known_ids:
                self.known_ids.add(id)
                return id

    def slugify(self, text):
        """Turn the text content of a header into a slug for use in an ID"""
        non_ascii = [c for c in text if ord(c) > 128]
        if non_ascii:
            for c in non_ascii:
                text = text.replace(c, self.encode_non_ascii(c))
        text = text.replace(' ', '_')
        return text

    def encode_non_ascii(self, c):
        # This is slightly gnarly.
        #
        # What MindTouch does is basically turn any non-ASCII characters
        # into UTF-8 codepoints, preceded by a dot.
        #
        # This is somewhat tricky in Python because Python's internals are
        # UCS-2, meaning that Python will give us, essentially, UTF-16
        # codepoints out of Unicode strings. So, an ugly but functional
        # hack: encode the offending character UTF-8 and repr that, which
        # gives us the codepoints preceded by '\x' escape sequences. Then
        # we can just replace the escape sequence with the dot, uppercase
        # it, and we have the thing MindTouch would generate.
        return repr(c.encode('utf-8')).strip("'").replace(r'\x', '.').upper()


    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        # Pass 1: Collect all known IDs from the stream
        buffer = []
        for token in input:
            buffer.append(token)
            if 'StartTag' == token['type']:
                attrs = dict(token['data'])
                if 'id' in attrs:
                    self.known_ids.add(attrs['id'])
                if 'name' in attrs:
                    self.known_ids.add(attrs['name'])

        # Pass 2: Sprinkle in IDs where they're needed
        while len(buffer):
            token = buffer.pop(0)
            
            if not ('StartTag' == token['type'] and
                    token['name'] in SECTION_TAGS):
                yield token
            else:
                attrs = dict(token['data'])
                
                # Treat a name attribute as a human-specified ID override
                name = attrs.get('name', None)
                if name:
                    attrs['id'] = name
                    token['data'] = attrs.items()
                    yield token
                    continue

                # If this is not a header, then generate a section ID.
                if token['name'] not in HEAD_TAGS:
                    attrs['id'] = self.gen_id()
                    token['data'] = attrs.items()
                    yield token
                    continue
                
                # If this is a header, then scoop up the rest of the header and
                # gather the text it contains.
                start, text, tmp = token, [], []
                while len(buffer):
                    token = buffer.pop(0)
                    tmp.append(token)
                    if token['type'] in ('Characters', 'SpaceCharacters'):
                        text.append(token['data'])
                    elif ('EndTag' == token['type'] and
                          start['name'] == token['name']):
                        # Note: This is naive, and doesn't track other
                        # start/end tags nested in the header. Odd things might
                        # happen in a case like <h1><h1></h1></h1>. But, that's
                        # invalid markup and the worst case should be a
                        # truncated ID because all the text wasn't accumulated.
                        break

                # Slugify the text we found inside the header, generate an ID
                # as a last resort.
                slug = self.slugify(u''.join(text))
                if not slug:
                    slug = self.gen_id()
                attrs['id'] = slug
                start['data'] = attrs.items()
                
                # Finally, emit the tokens we scooped up for the header.
                yield start
                for t in tmp:
                    yield t


class SectionEditLinkFilter(html5lib_Filter):
    """Filter which injects editing links for sections with IDs"""

    def __init__(self, source, full_path, locale):
        html5lib_Filter.__init__(self, source)
        self.full_path = full_path
        self.locale = locale

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        for token in input:

            yield token

            if ('StartTag' == token['type'] and
                    token['name'] in SECTION_TAGS):
                attrs = dict(token['data'])
                id = attrs.get('id', None)
                if id:
                    out = (
                        {'type': 'StartTag', 'name': 'a',
                         'data': {
                             'title': _('Edit section'),
                             'class': 'edit-section',
                             'data-section-id': id,
                             'data-section-src-url': u'%s?%s' % (
                                 reverse('wiki.document',
                                         args=[self.full_path],
                                         locale=self.locale),
                                 urlencode({'section': id.encode('utf-8'),
                                            'raw': 'true'})
                              ),
                              'href': u'%s?%s' % (
                                 reverse('wiki.edit_document',
                                         args=[self.full_path],
                                         locale=self.locale),
                                 urlencode({'section': id.encode('utf-8'),
                                            'edit_links': 'true'})
                              )
                         }},
                        {'type': 'Characters', 'data': _('Edit')},
                        {'type': 'EndTag', 'name': 'a'}
                    )
                    for t in out:
                        yield t


class SectionTOCFilter(html5lib_Filter):
    """Filter which builds a TOC tree of sections with headers"""
    def __init__(self, source):
        html5lib_Filter.__init__(self, source)
        self.level = 1
        self.in_header = False

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        for token in input:
            if ('StartTag' == token['type'] and token['name'] in HEAD_TAGS_TOC):
                self.in_header = True
                out = ()
                level_match = re.compile(r'^h(\d)$').match(token['name'])
                level = int(level_match.group(1))
                if level > self.level:
                    diff = level - self.level
                    for i in range(diff):
                        out += ({'type': 'StartTag', 'name': 'ol',
                                 'data': {}},)
                    self.level = level
                elif level < self.level:
                    diff = self.level - level
                    for i in range(diff):
                        out += ({'type': 'EndTag', 'name': 'li'},
                                {'type': 'EndTag', 'name': 'ol'})
                    self.level = level
                attrs = dict(token['data'])
                id = attrs.get('id', None)
                if id:
                    out += (
                        {'type': 'StartTag', 'name': 'li', 'data': {}},
                        {'type': 'StartTag', 'name': 'a',
                         'data': {
                            'rel': 'internal',
                            'href': '#%s' % id,
                         }},
                    )
                    for t in out:
                        yield t
            elif ('Characters' == token['type'] and self.in_header):
                yield token
            elif ('EndTag' == token['type'] and token['name'] in HEAD_TAGS_TOC):
                self.in_header = False
                level_match = re.compile(r'^h(\d)$').match(token['name'])
                level = int(level_match.group(1))
                out = ({'type': 'EndTag', 'name': 'a'},)
                for t in out:
                    yield t


class SectionFilter(html5lib_Filter):
    """Filter which can either extract the fragment representing a section by
    ID, or substitute a replacement stream for a section. Loosely based on
    HTML5 outline algorithm"""

    HEADING_TAGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hgroup')

    SECTION_TAGS = ('article', 'aside', 'nav', 'section', 'blockquote',
                    'body', 'details', 'fieldset', 'figure', 'table', 'div')

    def __init__(self, source, id, replace_source=None):
        html5lib_Filter.__init__(self, source)

        self.replace_source = replace_source
        self.section_id = id

        self.heading = None
        self.heading_rank = None
        self.open_level = 0
        self.parent_level = None
        self.in_section = False
        self.next_in_section = False
        self.replacement_emitted = False

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)
        for token in input:

            # Section start was deferred, so start it now.
            if self.next_in_section:
                self.next_in_section = False
                self.in_section = True

            if 'StartTag' == token['type']:
                attrs = dict(token['data'])
                self.open_level += 1

                # Have we encountered the section or heading element we're
                # looking for?
                if attrs.get('id', None) == self.section_id:

                    # If we encounter a section element that matches the ID,
                    # then we'll want to scoop up all its children as an
                    # explicit section.
                    if (self.parent_level is None and self._isSection(token)):
                        self.parent_level = self.open_level
                        # Defer the start of the section, so the section parent
                        # itself isn't included.
                        self.next_in_section = True

                    # If we encounter a heading element that matches the ID, we
                    # start an implicit section.
                    elif (self.heading is None and self._isHeading(token)):
                        self.heading = token
                        self.heading_rank = self._getHeadingRank(token)
                        self.parent_level = self.open_level - 1
                        self.in_section = True

                # If started an implicit section, these rules apply to
                # siblings...
                elif (self.heading is not None and
                        self.open_level - 1 == self.parent_level):

                    # The implicit section should stop if we hit another
                    # sibling heading whose rank is equal or higher, since that
                    # starts a new implicit section
                    if (self._isHeading(token) and
                            self._getHeadingRank(token) <= self.heading_rank):
                        self.in_section = False

            if 'EndTag' == token['type']:
                self.open_level -= 1

                # If the parent of the section has ended, end the section.
                # This applies to both implicit and explicit sections.
                if (self.parent_level is not None and
                        self.open_level < self.parent_level):
                    self.in_section = False

            # If there's no replacement source, then this is a section
            # extraction. So, emit tokens while we're in the section.
            if not self.replace_source:
                if self.in_section:
                    yield token

            # If there is a replacement source, then this is a section
            # replacement. Emit tokens of the source stream until we're in the
            # section, then emit the replacement stream and ignore the rest of
            # the source stream for the section..
            else:
                if not self.in_section:
                    yield token
                elif not self.replacement_emitted:
                    for r_token in self.replace_source:
                        yield r_token
                    self.replacement_emitted = True

    def _isHeading(self, token):
        """Is this token a heading element?"""
        return token['name'] in self.HEADING_TAGS

    def _isSection(self, token):
        """Is this token a section element?"""
        return token['name'] in self.SECTION_TAGS

    def _getHeadingRank(self, token):
        """Calculate the heading rank of this token"""
        if not self._isHeading(token):
            return None
        if 'hgroup' != token['name']:
            return int(token['name'][1])
        else:
            # FIXME: hgroup rank == highest rank of headers contained
            # But, we'd need to track the hgroup and then any child headers
            # encountered in the stream. Not doing that right now.
            # For now, just assume an hgroup is equivalent to h1
            return 1


class CodeSyntaxFilter(html5lib_Filter):
    """Filter which ensures section-related elements have unique IDs"""
    def __iter__(self):
        for token in html5lib_Filter.__iter__(self):
            if ('StartTag' == token['type']):
                if 'pre' == token['name']:
                    attrs = dict(token['data'])
                    function = attrs.get('function', None)
                    if function:
                        m = MT_SYNTAX_PAT.match(function)
                        if m:
                            lang = m.group(1).lower()
                            brush = MT_SYNTAX_BRUSH_MAP.get(lang, lang)
                            attrs['class'] = "brush: %s" % brush
                            del attrs['function']
                            token['data'] = attrs.items()
            yield token


class DekiscriptMacroFilter(html5lib_Filter):
    """Filter to convert Dekiscript template calls into kumascript macros."""
    def __iter__(self):

        buffer = []
        for token in html5lib_Filter.__iter__(self):
            buffer.append(token)

        while len(buffer):
            token = buffer.pop(0)

            if not ('StartTag' == token['type'] and
                    'span' == token['name']):
                yield token
                continue

            attrs = dict(token['data'])
            if attrs.get('class', '') != 'script':
                yield token
                continue

            ds_call = []
            while len(buffer):
                token = buffer.pop(0)
                if token['type'] in ('Characters', 'SpaceCharacters'):
                    ds_call.append(token['data'])
                elif 'StartTag' == token['type']:
                    attrs = token['data']
                    if attrs:
                        a_out = (u' %s' % u' '.join(
                            (u'%s=%s' % 
                             (name, quoteattr(val))
                             for name, val in attrs)))
                    else:
                        a_out = u''
                    ds_call.append(u'<%s%s>' % (token['name'], a_out))
                elif 'EndTag' == token['type']:
                    if 'span' == token['name']:
                        break
                    ds_call.append('</%s>' % token['name'])

            ds_call = u''.join(ds_call).strip()

            # Snip off any "template." prefixes
            strip_prefixes = ('template.', 'wiki.')
            for prefix in strip_prefixes:
                if ds_call.lower().startswith(prefix):
                    ds_call = ds_call[len(prefix):]

            # Convert numeric args to quoted. eg. bug(123) -> bug("123")
            num_re = re.compile(r'^([^(]+)\((\d+)')
            m = num_re.match(ds_call)
            if m:
                ds_call = '%s("%s")' % (m.group(1), m.group(2))

            # template("template name", [ "params" ])
            wt_re = re.compile(
                r'''^template\(['"]([^'"]+)['"],\s*\[([^\]]+)]''', re.I)
            m = wt_re.match(ds_call)
            if m:
                ds_call = '%s(%s)' % (m.group(1), m.group(2).strip())

            # template("template name")
            wt_re = re.compile(r'''^template\(['"]([^'"]+)['"]''', re.I)
            m = wt_re.match(ds_call)
            if m:
                ds_call = '%s()' % (m.group(1))

            # HACK: This is dirty, but seems like the easiest way to
            # reconstitute the token stream, including what gets parsed as
            # markup in the middle of macro parameters.
            #
            # eg. {{ Note("This is <strong>strongly</strong> discouraged") }}
            parsed = parse('{{ %s }}' % ds_call)
            for token in parsed.stream:
                yield token
