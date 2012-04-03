import logging
import re
from urllib import urlencode
import bleach

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter

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


def parse(src):
    return ContentSectionTool(src)


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
        return "".join(self.serializer.serialize(stream))

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

        # Pass 2: Sprinkle in IDs where they're missing
        for token in buffer:
            if ('StartTag' == token['type'] and
                    token['name'] in SECTION_TAGS):
                attrs = dict(token['data'])
                id = attrs.get('id', None)
                if not id:
                    attrs['id'] = self.gen_id()
                    token['data'] = attrs.items()
            yield token


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
                             'data-section-src-url': '%s?%s' % (
                                 reverse('wiki.document',
                                         args=[self.full_path],
                                         locale=self.locale),
                                 urlencode({'section': id, 'raw': 'true'})
                              ),
                              'href': '%s?%s' % (
                                 reverse('wiki.edit_document',
                                         args=[self.full_path],
                                         locale=self.locale),
                                 urlencode({'section': id,
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
            if ('StartTag' == token['type'] and token['name'] in HEAD_TAGS):
                self.in_header = True
                out = ()
                level_match = re.compile(r'^h(\d)$').match(token['name'])
                level = int(level_match.group(1))
                if level > self.level:
                    diff = level - self.level
                    for i in range(diff):
                        out += ({'type': 'StartTag', 'name': 'ol', 'data': {}},)
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
            elif ('EndTag' == token['type'] and token['name'] in HEAD_TAGS):
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
            if attrs.get('class','') != 'script':
                yield token
                continue

            ds_call = []
            while len(buffer) and 'EndTag' != token['type']:
                token = buffer.pop(0)
                if 'Characters' == token['type']:
                    ds_call.append(token['data'])

            ds_call = ''.join(ds_call).strip()

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
            wt_re = re.compile(r'''^template\(['"]([^'"]+)['"],\s*\[([^\]]+)]''', re.I)
            m = wt_re.match(ds_call)
            if m:
                ds_call = '%s(%s)' % (m.group(1), m.group(2).strip())

            # template("template name")
            wt_re = re.compile(r'''^template\(['"]([^'"]+)['"]''', re.I)
            m = wt_re.match(ds_call)
            if m:
                ds_call = '%s()' % (m.group(1))

            yield dict(
                type="Characters",
                data='{{ %s }}' % ds_call
            )
