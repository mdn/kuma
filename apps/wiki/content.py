# coding=utf-8

import logging
import re
import urllib
from urllib import urlencode
from urlparse import urlparse

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

# Head tags to be included in the table of contents
HEAD_TAGS_TOC = ('h2', 'h3', 'h4')

# Allowed tags in the table of contents list
TAGS_IN_TOC = ('code')

# Special paths within /docs/ URL-space that do not represent documents for the
# purposes of link annotation. Doesn't include everything from urls.py, but
# just the likely candidates for links.
DOC_SPECIAL_PATHS = ('new', 'tag', 'feeds', 'templates', 'needs-review')


def parse(src, is_full_document = False):
    return ContentSectionTool(src, is_full_document)


def get_content_sections(src=''):
    """Gets sections in a document, """
    sections = []

    if src:
        attr = '[id]'
        try:
            elements = pq(src).find(((attr + ',').join(SECTION_TAGS)) + attr)

            def objectify_pyquery_item(i):
                sections.append({'title': i.text(), 'id': i.attr('id')})

            elements.each(lambda e: objectify_pyquery_item(e))
        except:
            pass

    return sections


def get_seo_description(content, locale=None, strip_markup=True):
    # Create an SEO summary
    # TODO:  Google only takes the first 180 characters, so maybe we find a
    #        logical way to find the end of sentence before 180?
    seo_summary = ''
    try:
        if content:
            # Try constraining the search for summary to an explicit "Summary"
            # section, if any.
            summary_section = (parse(content)
                               .extractSection('Summary')
                               .serialize())
            if summary_section:
                content = summary_section

            # Need to add a BR to the page content otherwise pyQuery wont find
            # a <p></p> element if it's the only element in the doc_html
            seo_analyze_doc_html = content + '<br />'
            page = pq(seo_analyze_doc_html)

            # Look for the SEO summary class first
            summaryClasses = page.find('.seoSummary')
            if len(summaryClasses):
                if strip_markup:
                    seo_summary = summaryClasses.text()
                else:
                    seo_summary = summaryClasses.html()
            else:
                paragraphs = page.find('p')
                if paragraphs.length:
                    for p in range(len(paragraphs)):
                        item = paragraphs.eq(p)
                        if strip_markup:
                            text = item.text()
                        else:
                            text = item.html()
                        # Checking for a parent length of 2
                        # because we don't want p's wrapped
                        # in DIVs ("<div class='warning'>") and pyQuery adds
                        # "<html><div>" wrapping to entire document
                        if (text and len(text) and
                            not 'Redirect' in text and
                            text.find(u'«') == -1 and
                            text.find('&laquo') == -1 and
                            item.parents().length == 2):
                            seo_summary = text.strip()
                            break
    except:
        raise
        pass

    if strip_markup:
        # Post-found cleanup
        # remove markup chars
        seo_summary = seo_summary.replace('<', '').replace('>', '')
        # remove spaces around some punctuation added by PyQuery
        if locale == 'en-US':
            seo_summary = re.sub(r' ([,\)\.])', r'\1', seo_summary)
            seo_summary = re.sub(r'(\() ', r'\1', seo_summary)

    return seo_summary


def filter_out_noinclude(src):
    """Quick and dirty filter to remove <div class="noinclude"> blocks"""
    # NOTE: This started as an html5lib filter, but it started getting really
    # complex. Seems like pyquery works well enough without corrupting
    # character encoding.
    if not src:
        return ''
    doc = pq(src)
    doc.remove('*[class=noinclude]')
    return doc.html()


def extract_code_sample(id, src):
    """Extract a dict containing the html, css, and js listings for a given
    code sample identified by ID.

    This should be pretty agnostic to markup patterns, since it just requires a
    parent container with an DID and 3 child elements somewhere within with
    class names "html", "css", and "js" - and our syntax highlighting already
    does that with <pre>'s
    """
    parts = ('html', 'css', 'js')
    data = dict((x, None) for x in parts)
    if not src:
        return data
    try:
        section = parse(src).extractSection(id).serialize()
        if section:
            # HACK: Ensure the extracted section has a container, in case it
            # consists of a single element.
            sample = pq('<section>%s</section>' % section)
        else:
            # If no section, fall back to plain old ID lookup
            sample = pq(src).find('#%s' % id)
        for part in parts:
            selector = ','.join(x % (part,) for x in (
                '.%s',
                # HACK: syntaxhighlighter (ab)uses the className as a
                # semicolon-separated options list...
                'pre[class*="brush:%s"]',
                'pre[class*="%s;"]'
            ))
            src = sample.find(selector).text()
            if src is not None:
                # Bug 819999: &nbsp; gets decoded to \xa0, which trips up CSS
                src = src.replace(u'\xa0', u' ')
            data[part] = src
    except:
        pass
    return data


class ContentSectionTool(object):

    def __init__(self, src=None, is_full_document=False):

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
            self.parse(src, is_full_document)

    def parse(self, src, is_full_document):
        self.src = src
        if is_full_document:
            self.doc = self.parser.parse(self.src, parseMeta=True)
        else:
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

    def absolutizeAddresses(self, base_url, tag_attributes):
        self.stream = URLAbsolutionFilter(self.stream, base_url, tag_attributes)
        return self

    def annotateLinks(self, base_url):
        self.stream = LinkAnnotationFilter(self.stream, base_url)
        return self

    def filterIframeHosts(self, hosts):
        self.stream = IframeHostFilter(self.stream, hosts)
        return self

    def filterEditorSafety(self):
        self.stream = EditorSafetyFilter(self.stream)
        return self

    def extractSection(self, id):
        self.stream = SectionFilter(self.stream, id)
        return self

    def replaceSection(self, id, replace_src):
        replace_stream = self.walker(self.parser.parseFragment(replace_src))
        self.stream = SectionFilter(self.stream, id, replace_stream)
        return self

class URLAbsolutionFilter(html5lib_Filter):
    """Filter which turns relative links into absolute links.
       Originally created for teh purpose of sphinx templates."""

    def __init__(self, source, base_url, tag_attributes):
        html5lib_Filter.__init__(self, source)
        self.base_url = base_url
        self.tag_attributes = tag_attributes

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        for token in input:

            if ('StartTag' == token['type'] and token['name'] in self.tag_attributes):
                attrs = dict(token['data'])

                # If the element has the attribute we're looking for
                desired_attr = self.tag_attributes[token['name']]
                if desired_attr in attrs:
                    address = attrs[desired_attr]
                    if not address.startswith('http'):
                        # Starts with "/", so just add the base url
                        if address.startswith('//'):
                            #do nothing
                            attrs[desired_attr] = address
                        elif address.startswith('/'):
                            attrs[desired_attr] = self.base_url + address
                        else:
                            attrs[desired_attr] = self.base_url + '/' + address
                        token['data'] = attrs.items()

            yield token


class LinkAnnotationFilter(html5lib_Filter):
    """Filter which annotates links to indicate things like whether they're
    external, if they point to non-existent wiki pages, etc."""

    # TODO: Need more external link prefixes, here?
    EXTERNAL_PREFIXES = ('http:', 'https:', 'ftp:',)

    def __init__(self, source, base_url):
        html5lib_Filter.__init__(self, source)
        self.base_url = base_url

    def __iter__(self):
        from wiki.models import Document

        input = html5lib_Filter.__iter__(self)

        # Pass #1: Gather all the link URLs and prepare annotations
        links = dict()
        buffer = []
        for token in input:
            buffer.append(token)
            if ('StartTag' == token['type'] and 'a' == token['name']):
                attrs = dict(token['data'])
                if not 'href' in attrs:
                    continue

                href = attrs['href']
                if href.startswith(self.base_url):
                    # Squash site-absolute URLs to site-relative paths.
                    href = '/%s' % href[len(self.base_url):]

                # Prepare annotations record for this path.
                links[href] = dict(
                    classes=[]
                )

        # Run through all the links and check for annotatable conditions.
        for href in links.keys():

            # Is this an external URL?
            is_external = False
            for prefix in self.EXTERNAL_PREFIXES:
                if href.startswith(prefix):
                    is_external = True
                    break
            if is_external:
                links[href]['classes'].append('external')
                continue

            # TODO: Should this also check for old-school mindtouch URLs? Or
            # should we encourage editors to convert to new-style URLs to take
            # advantage of link annotation? (I'd say the latter)

            # Is this a kuma doc URL?
            if '/docs/' in href:

                # Check if this is a special docs path that's exempt from "new"
                skip = False
                for path in DOC_SPECIAL_PATHS:
                    if '/docs/%s' % path in href:
                        skip = True
                if skip:
                    continue

                href_locale, href_path = href.split(u'/docs/', 1)
                if href_locale.startswith(u'/'):
                    href_locale = href_locale[1:]

                if '#' in href_path:
                    # If present, discard the hash anchor
                    href_path, _, _ = href_path.partition('#')

                # Handle any URL-encoded UTF-8 characters in the path
                href_path = href_path.encode('utf-8', 'ignore')
                href_path = urllib.unquote(href_path)
                href_path = href_path.decode('utf-8', 'ignore')

                # Try to sort out the locale and slug through some of our
                # redirection logic.
                locale, slug, needs_redirect = (Document
                        .locale_and_slug_from_path(href_path,
                                                   path_locale=href_locale))

                # Does this locale and slug correspond to an existing document?
                # If not, mark it as a "new" link.
                #
                # TODO: Should these DB queries be batched up into one big
                # query? A page with hundreds of links will fire off hundreds
                # of queries
                ct = Document.objects.filter(locale=locale, slug=slug).count()
                if ct == 0:
                    links[href]['classes'].append('new')

        # Pass #2: Filter the content, annotating links
        for token in buffer:
            if ('StartTag' == token['type'] and 'a' == token['name']):
                attrs = dict(token['data'])

                if 'href' in attrs:

                    href = attrs['href']
                    if href.startswith(self.base_url):
                        # Squash site-absolute URLs to site-relative paths.
                        href = '/%s' % href[len(self.base_url):]

                    if href in links:
                        # Update class names on this link element.
                        if 'class' in attrs:
                            classes = set(attrs['class'].split(u' '))
                        else:
                            classes = set()
                        classes.update(links[href]['classes'])
                        if classes:
                            attrs['class'] = u' '.join(classes)

                token['data'] = attrs.items()

            yield token


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

    # MindTouch encodes these characters, so we have to encode them
    # too.
    non_url_safe = ['"', '#', '$', '%', '&', '+',
                    ',', '/', ':', ';', '=', '?',
                    '@', '[', '\\', ']', '^', '`',
                    '{', '|', '}', '~']

    def slugify(self, text):
        """Turn the text content of a header into a slug for use in an ID"""
        non_safe = [c for c in text if c in self.non_url_safe]
        if non_safe:
            for c in non_safe:
                text = text.replace(c, hex(ord(c)).replace('0x', '.').upper())
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
        self.level = 2
        self.in_header = False
        self.open_level = 0
        self.in_hierarchy = False
        self.max_level = 6

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        self.skip_header = False

        for token in input:
            if ('StartTag' == token['type'] and
                    token['name'] in HEAD_TAGS_TOC):
                level_match = re.compile(r'^h(\d)$').match(token['name'])
                level = int(level_match.group(1))
                if level > self.max_level:
                    self.skip_header = True
                    continue
                self.in_header = True
                out = ()
                if level > self.level:
                    diff = level - self.level
                    for i in range(diff):
                        if (not self.in_hierarchy and i % 2 == 0):
                            out += ({'type': 'StartTag', 'name': 'li',
                                     'data': {}},)
                        out += ({'type': 'StartTag', 'name': 'ol',
                                 'data': {}},)
                        if (diff > 1 and i % 2 == 0 and i != diff - 1):
                            out += ({'type': 'StartTag', 'name': 'li',
                                     'data': {}},)
                        self.open_level += 1
                    self.level = level
                elif level < self.level:
                    diff = self.level - level
                    for i in range(diff):
                        out += ({'type': 'EndTag', 'name': 'ol'},
                                {'type': 'EndTag', 'name': 'li'})
                        self.open_level -= 1
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
                    self.in_hierarchy = True
                    for t in out:
                        yield t
            elif ('StartTag' == token['type'] and
                  token['name'] in TAGS_IN_TOC and
                  not self.skip_header):
                yield token
            elif (token['type'] in ("Characters", "SpaceCharacters")
                  and self.in_header):
                yield token
            elif ('EndTag' == token['type'] and
                    token['name'] in TAGS_IN_TOC):
                yield token
            elif ('EndTag' == token['type'] and
                    token['name'] in HEAD_TAGS_TOC):
                level_match = re.compile(r'^h(\d)$').match(token['name'])
                level = int(level_match.group(1))
                if level > self.max_level:
                    self.skip_header = False
                    continue
                self.in_header = False
                out = ({'type': 'EndTag', 'name': 'a'},)
                for t in out:
                    yield t

        if self.open_level > 0:
            out = ()
            for i in range(self.open_level):
                out += ({'type': 'EndTag', 'name': 'ol'},
                        {'type': 'EndTag', 'name': 'li'})
            for t in out:
                yield t


class H2TOCFilter(SectionTOCFilter):
    def __init__(self, source):
        html5lib_Filter.__init__(self, source)
        self.level = 2
        self.max_level = 2
        self.in_header = False
        self.open_level = 0
        self.in_hierarchy = False


class H3TOCFilter(SectionTOCFilter):
    def __init__(self, source):
        html5lib_Filter.__init__(self, source)
        self.level = 2
        self.max_level = 3
        self.in_header = False
        self.open_level = 0
        self.in_hierarchy = False


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


class EditorSafetyFilter(html5lib_Filter):
    """Minimal filter meant to strip out harmful attributes and elements before
    rendering HTML for use in CKEditor"""
    def __iter__(self):

        for token in html5lib_Filter.__iter__(self):
        
            if ('StartTag' == token['type']):

                # Strip out any attributes that start with "on"
                token['data'] = [(k,v)
                    for (k,v) in dict(token['data']).items()
                    if not k.startswith('on')]

            yield token


class IframeHostFilter(html5lib_Filter):
    """Filter which scans through <iframe> tags and strips the src attribute if
    it doesn't contain a URL whose host matches a given list of allowed
    hosts. Also strips any markup found within <iframe></iframe>.
    """
    def __init__(self, source, hosts):
        html5lib_Filter.__init__(self, source)

        self.hosts = hosts

    def __iter__(self):
        in_iframe = False
        for token in html5lib_Filter.__iter__(self):
            if ('StartTag' == token['type']):
                if 'iframe' == token['name']:
                    in_iframe = True
                    attrs = dict(token['data'])
                    src = attrs.get('src', '')
                    if src:
                        if not re.search(self.hosts, src):
                            attrs['src'] = ''
                    token['data'] = attrs.items()
                    yield token
            if ('EndTag' == token['type']):
                if 'iframe' == token['name']:
                    in_iframe = False
            if not in_iframe:
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
