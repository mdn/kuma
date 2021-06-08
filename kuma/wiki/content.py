from xml.sax.saxutils import quoteattr

import html5lib
import newrelic.agent
from html5lib.filters.base import Filter as html5lib_Filter

from kuma.core.utils import safer_pyquery as pq


# List of tags supported for section editing. A subset of everything that could
# be considered an HTML5 section
SECTION_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "hgroup", "section")


class Extractor(object):
    def __init__(self, document):
        self.document = document

    @newrelic.agent.function_trace()
    def code_sample(self, name):
        """
        Extract a dict containing the html, css, and js listings for a given
        code sample identified by a name.

        This should be pretty agnostic to markup patterns, since it just
        requires a parent container with an DID and 3 child elements somewhere
        within with class names "html", "css", and "js" - and our syntax
        highlighting already does that with <pre>'s

        Given the name of a code sample, attempt to extract it from rendered
        HTML with a fallback to non-rendered in case of errors.
        """
        parts = ("html", "css", "js")
        data = dict((x, None) for x in parts)

        doc = self.document

        if doc.rendered_html and not getattr(doc, "rendered_errors", False):
            src = doc.rendered_html
        elif doc.html:
            src = doc.html
        else:
            return data

        section = parse(src).extractSection(name).serialize()
        if section:
            # HACK: Ensure the extracted section has a container, in case it
            # consists of a single element.
            sample = pq("<section>%s</section>" % section)
        else:
            # If no section, fall back to plain old ID lookup
            try:
                sample = pq(src).find("[id=%s]" % quoteattr(name))
            except ValueError:
                return data

        selector_templates = (
            ".%s",
            # HACK: syntaxhighlighter (ab)uses the className as a
            # semicolon-separated options list...
            'pre[class*="brush:%s"]',
            'pre[class*="%s;"]',
        )
        for part in parts:
            selector = ",".join(
                selector_template % part for selector_template in selector_templates
            )
            src = sample.find(selector).text(squash_space=False)
            if src is not None:
                # Bug 819999: &nbsp; gets decoded to \xa0, which trips up CSS
                src = src.replace("\xa0", " ")
                # Bug 1284781: &nbsp; is incorrectly parsed on embed sample
                src = src.replace("&nbsp;", " ")
            if src:
                data[part] = src

        return data


class ContentSectionTool(object):
    def __init__(self, src=None, is_full_document=False):

        self.tree = html5lib.treebuilders.getTreeBuilder("etree")

        self.parser = html5lib.HTMLParser(tree=self.tree, namespaceHTMLElements=False)

        self._serializer = None
        self._default_serializer_options = {
            "omit_optional_tags": False,
            "quote_attr_values": "always",
            "escape_lt_in_attrs": True,
            "alphabetical_attributes": True,
        }
        self._serializer_options = None
        self.walker = html5lib.treewalkers.getTreeWalker("etree")

        self.src = ""
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

    def _get_serializer(self, **options):
        soptions = self._default_serializer_options.copy()
        soptions.update(options)
        if not (self._serializer and self._serializer_options == soptions):
            self._serializer = html5lib.serializer.HTMLSerializer(**soptions)
            self._serializer_options = soptions
        return self._serializer

    def serialize(self, stream=None, **options):
        if stream is None:
            stream = self.stream
        return "".join(self._get_serializer(**options).serialize(stream))

    def __str__(self):
        return self.serialize()

    def filter(self, filter_cls):
        self.stream = filter_cls(self.stream)
        return self

    @newrelic.agent.function_trace()
    def extractSection(self, id, ignore_heading=False):
        self.stream = SectionFilter(self.stream, id, ignore_heading=ignore_heading)
        return self


class SectionFilter(html5lib_Filter):
    """
    Filter which can either extract the fragment representing a section by
    ID, or substitute a replacement stream for a section. Loosely based on
    HTML5 outline algorithm
    """

    HEADING_TAGS = ("h1", "h2", "h3", "h4", "h5", "h6", "hgroup")

    SECTION_TAGS = (
        "article",
        "aside",
        "nav",
        "section",
        "blockquote",
        "body",
        "details",
        "fieldset",
        "figure",
        "table",
        "div",
    )

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

            if token["type"] == "StartTag":
                attrs = dict(token["data"])
                self.open_level += 1

                # Have we encountered the section or heading element we're
                # looking for?
                if self.section_id in attrs.values():

                    # If we encounter a section element that matches the ID,
                    # then we'll want to scoop up all its children as an
                    # explicit section.
                    if self.parent_level is None and self._isSection(token):
                        self.parent_level = self.open_level
                        # Defer the start of the section, so the section parent
                        # itself isn't included.
                        self.next_in_section = True

                    # If we encounter a heading element that matches the ID, we
                    # start an implicit section.
                    elif self.heading is None and self._isHeading(token):
                        self.heading = token
                        self.heading_rank = self._getHeadingRank(token)
                        self.parent_level = self.open_level - 1
                        self.in_section = True

                # If started an implicit section, these rules apply to
                # siblings...
                elif (
                    self.heading is not None
                    and self.open_level - 1 == self.parent_level
                ):

                    # The implicit section should stop if we hit another
                    # sibling heading whose rank is equal or higher, since that
                    # starts a new implicit section
                    if (
                        self._isHeading(token)
                        and self._getHeadingRank(token) <= self.heading_rank
                    ):
                        self.in_section = False

                # If this is the first heading of the section and we want to
                # omit it, note that we've found it
                is_first_heading = (
                    self.in_section
                    and self.ignore_heading
                    and not self.already_ignored_header
                    and not self.heading_to_ignore
                    and self._isHeading(token)
                )
                if is_first_heading:
                    self.heading_to_ignore = token

            elif token["type"] == "EndTag":
                self.open_level -= 1

                # If the parent of the section has ended, end the section.
                # This applies to both implicit and explicit sections.
                if (
                    self.parent_level is not None
                    and self.open_level < self.parent_level
                ):
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
            if (
                token["type"] == "EndTag"
                and self.in_section
                and self.ignore_heading
                and not self.already_ignored_header
                and self.heading_to_ignore
                and self._isHeading(token)
                and token["name"] == self.heading_to_ignore["name"]
            ):

                self.heading_to_ignore = None
                self.already_ignored_header = True

    def _isHeading(self, token):
        """Is this token a heading element?"""
        return token["name"] in self.HEADING_TAGS

    def _isSection(self, token):
        """Is this token a section element?"""
        return token["name"] in self.SECTION_TAGS

    def _getHeadingRank(self, token):
        """Calculate the heading rank of this token"""
        if not self._isHeading(token):
            return None
        if token["name"] != "hgroup":
            return int(token["name"][1])
        else:
            # FIXME: hgroup rank == highest rank of headers contained
            # But, we'd need to track the hgroup and then any child headers
            # encountered in the stream. Not doing that right now.
            # For now, just assume an hgroup is equivalent to h1
            return 1


_content_section_tool = ContentSectionTool()


@newrelic.agent.function_trace()
def parse(src, is_full_document=False):
    return _content_section_tool.parse(src, is_full_document)
