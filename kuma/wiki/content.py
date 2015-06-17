# -*- coding: utf-8 -*-
from collections import defaultdict
import re
import urllib
from urllib import urlencode
from urlparse import urlparse

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter
import newrelic.agent
from lxml import etree
from pyquery import PyQuery as pq

from tower import ugettext as _

from kuma.core.urlresolvers import reverse
from .utils import locale_and_slug_from_path

# A few regex patterns for various parsing efforts in this file
MACRO_RE = re.compile(r'\{\{\s*([^\(\} ]+)', re.MULTILINE)

LEVEL_RE = re.compile(r'^h(\d)$')

TEMPLATE_PARAMS_RE = re.compile(r'''^template\(['"]([^'"]+)['"],\s*\[([^\]]+)]''', re.I)

TEMPLATE_RE = re.compile(r'''^template\(['"]([^'"]+)['"]''', re.I)

# Regex to extract language from MindTouch code elements' function attribute
MT_SYNTAX_RE = re.compile(r'syntax\.(\w+)')
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


@newrelic.agent.function_trace()
def parse(src, is_full_document=False):
    return ContentSectionTool(src, is_full_document)


@newrelic.agent.function_trace()
def get_content_sections(src=''):
    """
    Gets sections in a document
    """
    sections = []
    if src:
        attr = '[id]'
        selector = (attr + ',').join(SECTION_TAGS) + attr
        try:
            document = pq(src)
        except etree.ParserError:
            pass
        else:
            for element in document.find(selector):
                sections.append({'title': element.text,
                                 'id': element.attrib.get('id')})
    return sections


@newrelic.agent.function_trace()
def get_seo_description(content, locale=None, strip_markup=True):
    # Create an SEO summary
    # TODO:  Google only takes the first 180 characters, so maybe we find a
    #        logical way to find the end of sentence before 180?
    seo_summary = ''
    if content:
        # Try constraining the search for summary to an explicit "Summary"
        # section, if any.
        summary_section = (parse(content).extractSection('Summary')
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
                            'Redirect' not in text and
                            text.find(u'«') == -1 and
                            text.find('&laquo') == -1 and
                            item.parents().length == 2):
                        seo_summary = text.strip()
                        break

    if strip_markup:
        # Post-found cleanup
        # remove markup chars
        seo_summary = seo_summary.replace('<', '').replace('>', '')
        # remove spaces around some punctuation added by PyQuery
        if locale == 'en-US':
            seo_summary = re.sub(r' ([,\)\.])', r'\1', seo_summary)
            seo_summary = re.sub(r'(\() ', r'\1', seo_summary)

    return seo_summary


@newrelic.agent.function_trace()
def filter_out_noinclude(src):
    """
    Quick and dirty filter to remove <div class="noinclude"> blocks
    """
    # NOTE: This started as an html5lib filter, but it started getting really
    # complex. Seems like pyquery works well enough without corrupting
    # character encoding.
    if not src:
        return ''
    doc = pq(src)
    doc.remove('*[class=noinclude]')
    return doc.html()


@newrelic.agent.function_trace()
def extract_code_sample(id, src):
    """
    Extract a dict containing the html, css, and js listings for a given
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
        if src:
            data[part] = src

    return data


@newrelic.agent.function_trace()
def extract_css_classnames(content):
    """
    Extract the unique set of class names used in the content
    """
    classnames = set()
    for element in pq(content).find('*'):
        css_classes = element.attrib.get('class')
        if css_classes:
            classnames.update(css_classes.split(' '))
    return list(classnames)


@newrelic.agent.function_trace()
def extract_html_attributes(content):
    """
    Extract the unique set of HTML attributes used in the content
    """
    try:
        attribs = []
        for token in parse(content).stream:
            if token['type'] == 'StartTag':
                for (namespace, name), value in token['data'].items():
                    attribs.append((name, value))
        return ['%s="%s"' % (k, v) for k, v in attribs]
    except:
        return []


@newrelic.agent.function_trace()
def extract_kumascript_macro_names(content):
    """
    Extract a unique set of KumaScript macro names used in the content
    """
    names = set()
    try:
        txt = []
        for token in parse(content).stream:
            if token['type'] in ('Characters', 'SpaceCharacters'):
                txt.append(token['data'])
        txt = ''.join(txt)
        names.update(MACRO_RE.findall(txt))
    except:
        pass
    return list(names)


class ContentSectionTool(object):

    def __init__(self, src=None, is_full_document=False):

        self.tree = html5lib.treebuilders.getTreeBuilder("etree")

        self.parser = html5lib.HTMLParser(tree=self.tree,
                                          namespaceHTMLElements=False)

        self.serializer = html5lib.serializer.htmlserializer.HTMLSerializer(
            omit_optional_tags=False, quote_attr_values=True,
            escape_lt_in_attrs=True)

        self.walker = html5lib.treewalkers.getTreeWalker("etree")

        self.src = ''
        self.doc = None
        self.stream = []

        if src:
            self.parse(src, is_full_document)

    @newrelic.agent.function_trace()
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

    @newrelic.agent.function_trace()
    def injectSectionIDs(self):
        self.stream = SectionIDFilter(self.stream)
        return self

    @newrelic.agent.function_trace()
    def injectSectionEditingLinks(self, slug, locale):
        self.stream = SectionEditLinkFilter(self.stream, slug, locale)
        return self

    @newrelic.agent.function_trace()
    def absolutizeAddresses(self, base_url, tag_attributes):
        self.stream = URLAbsolutionFilter(self.stream, base_url, tag_attributes)
        return self

    @newrelic.agent.function_trace()
    def annotateLinks(self, base_url):
        self.stream = LinkAnnotationFilter(self.stream, base_url)
        return self

    @newrelic.agent.function_trace()
    def filterIframeHosts(self, hosts):
        self.stream = IframeHostFilter(self.stream, hosts)
        return self

    @newrelic.agent.function_trace()
    def filterEditorSafety(self):
        self.stream = EditorSafetyFilter(self.stream)
        return self

    @newrelic.agent.function_trace()
    def extractSection(self, id, ignore_heading=False):
        self.stream = SectionFilter(self.stream, id,
                                    ignore_heading=ignore_heading)
        return self

    @newrelic.agent.function_trace()
    def replaceSection(self, id, replace_src, ignore_heading=False):
        replace_stream = self.walker(self.parser.parseFragment(replace_src))
        self.stream = SectionFilter(self.stream, id, replace_stream,
                                    ignore_heading=ignore_heading)
        return self


class URLAbsolutionFilter(html5lib_Filter):
    """
    Filter which turns relative links into absolute links.
    Originally created for generating sphinx templates.
    """
    def __init__(self, source, base_url, tag_attributes):
        html5lib_Filter.__init__(self, source)
        self.base_url = base_url
        self.tag_attributes = tag_attributes

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        for token in input:

            if (token['type'] == 'StartTag' and
                    token['name'] in self.tag_attributes):
                attrs = dict(token['data'])

                # If the element has the attribute we're looking for
                desired_attr = self.tag_attributes[token['name']]

                for (namespace, name), value in attrs.items():
                    if desired_attr == name:
                        if not value.startswith('http'):
                            if value.startswith('//') or value.startswith('{{'):
                                # Do nothing for absolute addresses or apparent
                                # template variable output
                                attrs[(namespace, name)] = value
                            elif value.startswith('/'):
                                # Starts with "/", so just add the base url
                                attrs[(namespace, name)] = self.base_url + value
                            else:
                                attrs[(namespace, name)] = self.base_url + '/' + value
                            token['data'] = attrs
                        break

            yield token


class LinkAnnotationFilter(html5lib_Filter):
    """
    Filter which annotates links to indicate things like whether they're
    external, if they point to non-existent wiki pages, etc.
    """
    # TODO: Need more external link prefixes, here?
    EXTERNAL_PREFIXES = ('http:', 'https:', 'ftp:',)

    def __init__(self, source, base_url):
        html5lib_Filter.__init__(self, source)
        self.base_url = base_url
        self.base_url_parsed = urlparse(base_url)

    def __iter__(self):
        from kuma.wiki.models import Document

        input = html5lib_Filter.__iter__(self)

        # Pass #1: Gather all the link URLs and prepare annotations
        links = {}
        buffer = []
        for token in input:
            buffer.append(token)
            if token['type'] == 'StartTag' and token['name'] == 'a':
                for (namespace, name), value in token['data'].items():
                    if name == 'href':
                        href = value
                        href_parsed = urlparse(href)
                        if href_parsed.netloc == self.base_url_parsed.netloc:
                            # Squash site-absolute URLs to site-relative paths.
                            href = href_parsed.path

                        # Prepare annotations record for this path.
                        links[href] = {'classes': []}

        needs_existence_check = defaultdict(lambda: defaultdict(set))

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
                locale, slug, needs_redirect = (
                    locale_and_slug_from_path(href_path,
                                              path_locale=href_locale))

                # Gather up this link for existence check
                needs_existence_check[locale.lower()][slug.lower()].add(href)

        # Perform existence checks for all the links, using one DB query per
        # locale for all the candidate slugs.
        for locale, slug_hrefs in needs_existence_check.items():

            existing_slugs = (Document.objects
                                      .filter(locale=locale,
                                              slug__in=slug_hrefs.keys())
                                      .values_list('slug', flat=True))

            # Remove the slugs that pass existence check.
            for slug in existing_slugs:
                lslug = slug.lower()
                if lslug in slug_hrefs:
                    del slug_hrefs[lslug]

            # Mark all the links whose slugs did not come back from the DB
            # query as "new"
            for slug, hrefs in slug_hrefs.items():
                for href in hrefs:
                    links[href]['classes'].append('new')

        # Pass #2: Filter the content, annotating links
        for token in buffer:
            if token['type'] == 'StartTag' and token['name'] == 'a':
                attrs = dict(token['data'])
                names = [name for (namespace, name) in attrs.keys()]
                for (namespace, name), value in attrs.items():
                    if name == 'href':
                        href = value
                        href_parsed = urlparse(value)
                        if href_parsed.netloc == self.base_url_parsed.netloc:
                            # Squash site-absolute URLs to site-relative paths.
                            href = href_parsed.path

                        if href in links:
                            # Update class names on this link element.
                            if 'class' in names:
                                classes = set(attrs[(namespace, 'class')].split(u' '))
                            else:
                                classes = set()
                            classes.update(links[href]['classes'])
                            if classes:
                                attrs[(namespace, u'class')] = u' '.join(classes)

                token['data'] = attrs

            yield token


class SectionIDFilter(html5lib_Filter):
    """
    Filter which ensures section-related elements have unique IDs
    """
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
        """
        Turn the text content of a header into a slug for use in an ID
        """
        non_safe = [c for c in text if c in self.non_url_safe]
        if non_safe:
            for c in non_safe:
                text = text.replace(c, '')
        # Strip leading, trailing and multiple whitespace, convert remaining whitespace to _
        text = u'_'.join(text.split())
        return text

    def process_header(self, token, buffer):
        # If we get into this code, 'token' will be the start tag of a
        # header element. We're going to grab its text contents to
        # generate a slugified ID for it, add that ID in, and then
        # spit it back out. 'buffer' is the list of tokens we were in
        # the process of handling when we hit this header.
        start, text, tmp = token, [], []
        attrs = dict(token['data'])
        while len(buffer):
            # Loop through successive tokens in the stream of HTML
            # until we find our end tag, building up in 'tmp' a list
            # of those tokens to emit later, and in 'text' a list of
            # the text content we see along the way.
            next_token = buffer.pop(0)
            tmp.append(next_token)
            if next_token['type'] in ('Characters', 'SpaceCharacters'):
                text.append(next_token['data'])
            elif (next_token['type'] == 'EndTag' and
                  next_token['name'] == start['name']):
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
        else:
            # Create unique slug for heading tags with the same content
            start_inc = 2
            slug_base = slug
            while slug in self.known_ids:
                slug = u'{0}_{1}'.format(slug_base, start_inc)
                start_inc += 1

        attrs[(None, u'id')] = slug
        start['data'] = attrs
        self.known_ids.add(slug)

        # Hand back buffer minus the bits we yanked out of it, and the
        # new ID-ified header start tag and contents.
        return buffer, [start] + tmp

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        # First, collect all ID values already in the source HTML.
        buffer = []
        for token in input:
            buffer.append(token)
            if token['type'] == 'StartTag':
                attrs = dict(token['data'])
                for (namespace, name), value in attrs.items():
                    # Collect both 'name' and 'id' attributes since
                    # 'name' gets treated as a manual override to
                    # specify an ID.
                    if name == 'id' and token['name'] not in HEAD_TAGS:
                        self.known_ids.add(value)
                    if name == 'name':
                        self.known_ids.add(value)

        # Then walk the tree again identifying elements in need of IDs
        # and adding them.
        while len(buffer):
            token = buffer.pop(0)

            if not (token['type'] == 'StartTag' and
                    token['name'] in SECTION_TAGS):
                # If this token isn't the start tag of a section or
                # header, we don't add an ID and just short-circuit
                # out to return the token as-is.
                yield token
            else:
                # Potential bug warning: there may not be any
                # attributes, so doing a for loop over them to look
                # for existing ID/name values is unsafe. Instead we
                # dict-ify the attrs, and then check directly for the
                # things we care about instead of iterating all
                # attributes and waiting for one we care about to show
                # up.
                attrs = dict(token['data'])

                # First check for a 'name' attribute; if it's present,
                # treat it as a manual override by the author and make
                # that value be the ID.
                if (None, 'name') in attrs:
                    attrs[(None, u'id')] = attrs[(None, 'name')]
                    token['data'] = attrs
                    yield token
                    continue
                # Next look for <section> tags which don't have an ID
                # set; since we don't generate an ID for them from
                # their text contents, they just get a numeric one
                # from gen_id().
                if token['name'] not in HEAD_TAGS:
                    if (None, 'id') not in attrs:
                        attrs[(None, u'id')] = self.gen_id()
                        token['data'] = attrs
                    yield token
                    continue
                # If we got here, we're looking at the start tag of a
                # header which had no 'name' attribute set. We're
                # going to pop out the text contents of the header,
                # use them to generate a slugified ID for it, and
                # return it with that ID added in.
                buffer, header_tokens = self.process_header(token, buffer)
                for t in header_tokens:
                    yield t


class SectionEditLinkFilter(html5lib_Filter):
    """
    Filter which injects editing links for sections with IDs
    """
    def __init__(self, source, slug, locale):
        html5lib_Filter.__init__(self, source)
        self.slug = slug
        self.locale = locale

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)

        for token in input:

            yield token

            if (token['type'] == 'StartTag' and
                    token['name'] in SECTION_TAGS):
                attrs = dict(token['data'])
                for (namespace, name), value in attrs.items():
                    if name == 'id' and value:
                        ts = ({'type': 'StartTag',
                               'name': 'a',
                               'data': {
                                   (None, u'title'): _('Edit section'),
                                   (None, u'class'): 'edit-section',
                                   (None, u'data-section-id'): value,
                                   (None, u'data-section-src-url'): u'%s?%s' % (
                                       reverse('wiki.document',
                                               args=[self.slug],
                                               locale=self.locale),
                                       urlencode({'section': value.encode('utf-8'),
                                                  'raw': 'true'})
                                   ),
                                   (None, u'href'): u'%s?%s' % (
                                       reverse('wiki.edit_document',
                                               args=[self.slug],
                                               locale=self.locale),
                                       urlencode({'section': value.encode('utf-8'),
                                                  'edit_links': 'true'})
                                   )
                               }},
                              {'type': 'Characters',
                               'data': _(u'Edit')},
                              {'type': 'EndTag', 'name': 'a'})
                        for t in ts:
                            yield t


class SectionTOCFilter(html5lib_Filter):
    """
    Filter which builds a TOC tree of sections with headers
    """
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
            if (token['type'] == 'StartTag' and
                    token['name'] in HEAD_TAGS_TOC):
                level_match = LEVEL_RE.match(token['name'])
                level = int(level_match.group(1))
                if level > self.max_level:
                    self.skip_header = True
                    continue
                self.in_header = True
                out = []
                if level > self.level:
                    diff = level - self.level
                    for i in range(diff):
                        if (not self.in_hierarchy and i % 2 == 0):
                            out.append({'type': 'StartTag',
                                        'name': 'li',
                                        'data': {}})
                        out.append({'type': 'StartTag',
                                    'name': 'ol',
                                    'data': {}})
                        if (diff > 1 and i % 2 == 0 and i != diff - 1):
                            out.append({'type': 'StartTag',
                                        'name': 'li',
                                        'data': {}})
                        self.open_level += 1
                    self.level = level
                elif level < self.level:
                    diff = self.level - level
                    for i in range(diff):
                        out.extend([{'type': 'EndTag',
                                    'name': 'ol'},
                                    {'type': 'EndTag',
                                     'name': 'li'}])
                        self.open_level -= 1
                    self.level = level
                attrs = dict(token['data'])
                id = attrs.get((None, 'id'), None)
                if id:
                    out.extend([
                        {'type': 'StartTag', 'name': 'li', 'data': {}},
                        {'type': 'StartTag', 'name': 'a',
                         'data': {(None, u'rel'): 'internal',
                                  (None, u'href'): '#%s' % id}},
                    ])
                    self.in_hierarchy = True
                    for t in out:
                        yield t
            elif (token['type'] == 'StartTag' and
                  token['name'] in TAGS_IN_TOC and
                  self.in_header and
                  not self.skip_header):
                yield token
            elif (token['type'] in ("Characters", "SpaceCharacters")
                  and self.in_header):
                yield token
            elif (token['type'] == 'EndTag' and
                  token['name'] in TAGS_IN_TOC and
                  self.in_header):
                yield token
            elif (token['type'] == 'EndTag' and
                    token['name'] in HEAD_TAGS_TOC):
                level_match = LEVEL_RE.match(token['name'])
                level = int(level_match.group(1))
                if level > self.max_level:
                    self.skip_header = False
                    continue
                self.in_header = False
                yield {'type': 'EndTag', 'name': 'a'}

        if self.open_level > 0:
            out = []
            for i in range(self.open_level):
                out.extend([{'type': 'EndTag', 'name': 'ol'},
                            {'type': 'EndTag', 'name': 'li'}])
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
    """
    Filter which can either extract the fragment representing a section by
    ID, or substitute a replacement stream for a section. Loosely based on
    HTML5 outline algorithm
    """
    HEADING_TAGS = ('h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'hgroup')

    SECTION_TAGS = ('article', 'aside', 'nav', 'section', 'blockquote',
                    'body', 'details', 'fieldset', 'figure', 'table', 'div')

    def __init__(self, source, id, replace_source=None, ignore_heading=False):
        html5lib_Filter.__init__(self, source)

        self.replace_source = replace_source
        self.ignore_heading = ignore_heading
        self.section_id = id

        self.heading = None
        self.heading_rank = None
        self.open_level = 0
        self.parent_level = None
        self.in_section = False
        self.heading_to_ignore = None
        self.already_ignored_header = False
        self.next_in_section = False
        self.replacement_emitted = False

    def __iter__(self):
        input = html5lib_Filter.__iter__(self)
        for token in input:

            # Section start was deferred, so start it now.
            if self.next_in_section:
                self.next_in_section = False
                self.in_section = True

            if token['type'] == 'StartTag':
                attrs = dict(token['data'])
                self.open_level += 1

                # Have we encountered the section or heading element we're
                # looking for?
                if self.section_id in attrs.values():

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

                # If this is the first heading of the section and we want to
                # omit it, note that we've found it
                if (self.in_section and
                        self.ignore_heading and
                        not self.already_ignored_header and
                        not self.heading_to_ignore and
                        self._isHeading(token)):

                    self.heading_to_ignore = token

            elif token['type'] == 'EndTag':
                self.open_level -= 1

                # If the parent of the section has ended, end the section.
                # This applies to both implicit and explicit sections.
                if (self.parent_level is not None and
                        self.open_level < self.parent_level):
                    self.in_section = False

            # If there's no replacement source, then this is a section
            # extraction. So, emit tokens while we're in the section, as long
            # as we're also not in the process of ignoring a heading
            if not self.replace_source:
                if self.in_section and not self.heading_to_ignore:
                    yield token

            # If there is a replacement source, then this is a section
            # replacement. Emit tokens of the source stream until we're in the
            # section, then emit the replacement stream and ignore the rest of
            # the source stream for the section. Note that an ignored heading
            # is *not* replaced.
            else:
                if not self.in_section or self.heading_to_ignore:
                    yield token
                elif not self.replacement_emitted:
                    for r_token in self.replace_source:
                        yield r_token
                    self.replacement_emitted = True

            # If this looks like the end of a heading we were ignoring, clear
            # the ignoring condition.
            if (token['type'] == 'EndTag' and
                    self.in_section and
                    self.ignore_heading and
                    not self.already_ignored_header and
                    self.heading_to_ignore and
                    self._isHeading(token) and
                    token['name'] == self.heading_to_ignore['name']):

                self.heading_to_ignore = None
                self.already_ignored_header = True

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
        if token['name'] != 'hgroup':
            return int(token['name'][1])
        else:
            # FIXME: hgroup rank == highest rank of headers contained
            # But, we'd need to track the hgroup and then any child headers
            # encountered in the stream. Not doing that right now.
            # For now, just assume an hgroup is equivalent to h1
            return 1


class CodeSyntaxFilter(html5lib_Filter):
    """
    Filter which ensures section-related elements have unique IDs
    """
    def __iter__(self):
        for token in html5lib_Filter.__iter__(self):
            if token['type'] == 'StartTag' and token['name'] == 'pre':
                attrs = dict(token['data'])
                for (namespace, name), value in attrs.items():
                    if name == 'function' and value:
                        m = MT_SYNTAX_RE.match(value)
                        if m:
                            lang = m.group(1).lower()
                            brush = MT_SYNTAX_BRUSH_MAP.get(lang, lang)
                            attrs[(namespace, u'class')] = "brush: %s" % brush
                            del attrs[(None, 'function')]
                            token['data'] = attrs
            yield token


class EditorSafetyFilter(html5lib_Filter):
    """
    Minimal filter meant to strip out harmful attributes and elements before
    rendering HTML for use in CKEditor
    """
    def __iter__(self):
        for token in html5lib_Filter.__iter__(self):
            if token['type'] == 'StartTag':
                # Strip out any attributes that start with "on"
                attrs = {}
                for (namespace, name), value in token['data'].items():
                    if name.startswith('on'):
                        continue
                    attrs[(namespace, name)] = value
                token['data'] = attrs
            yield token


class IframeHostFilter(html5lib_Filter):
    """
    Filter which scans through <iframe> tags and strips the src attribute if
    it doesn't contain a URL whose host matches a given list of allowed
    hosts. Also strips any markup found within <iframe></iframe>.
    """
    def __init__(self, source, hosts):
        html5lib_Filter.__init__(self, source)
        self.hosts = hosts

    def __iter__(self):
        in_iframe = False
        for token in html5lib_Filter.__iter__(self):
            if token['type'] == 'StartTag' and token['name'] == 'iframe':
                in_iframe = True
                attrs = dict(token['data'])
                for (namespace, name), value in attrs.items():
                    if name == 'src' and value:
                        if not re.search(self.hosts, value):
                            attrs[(namespace, 'src')] = ''
                    token['data'] = attrs
                yield token
            if token['type'] == 'EndTag' and token['name'] == 'iframe':
                in_iframe = False
            if not in_iframe:
                yield token
