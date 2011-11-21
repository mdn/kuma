from copy import deepcopy

from django.conf import settings

from nose.tools import eq_
from pyquery import PyQuery as pq

from gallery.models import Video
from gallery.tests import image, video
from sumo.tests import TestCase
from devmo.tests import SkippedTestCase
import sumo.tests.test_parser
from wiki.parser import (WikiParser, ForParser, PATTERNS, RECURSION_MESSAGE,
                         _build_template_params as _btp,
                         _format_template_content as _ftc, _key_split)
from wiki.tests import document, revision


def doc_rev_parser(*args, **kwargs):
    return sumo.tests.test_parser.doc_rev_parser(*args, parser_cls=WikiParser,
                                                 **kwargs)


def doc_parse_markup(content, markup, title='Template:test'):
    """Create a doc with given content and parse given markup."""
    _, _, p = doc_rev_parser(content, title)
    doc = pq(p.parse(markup))
    return (doc, p)


class SimpleSyntaxTestCase(SkippedTestCase):
    """Simple syntax regexing, like {note}...{/note}, {key Ctrl+K}"""
    fixtures = ['users.json']

    def test_note_simple(self):
        """Simple note syntax"""
        p = WikiParser()
        doc = pq(p.parse('{note}this is a note{/note}'))
        eq_('this is a note', doc('div.note').text())

    def test_warning_simple(self):
        """Simple warning syntax"""
        p = WikiParser()
        doc = pq(p.parse('{warning}this is a warning{/warning}'))
        eq_('this is a warning', doc('div.warning').text())

    def test_warning_multiline(self):
        """Multiline warning syntax"""
        p = WikiParser()
        doc = pq(p.parse('{warning}\nthis is a warning\n{/warning}'))
        eq_('this is a warning', doc('div.warning').text())

    def test_warning_multiline_breaks(self):
        """Multiline breaks warning syntax"""
        p = WikiParser()
        doc = pq(p.parse('\n\n{warning}\n\nthis is a warning\n\n'
                         '{/warning}\n\n'))
        eq_('this is a warning', doc('div.warning').text())

    def test_general_warning_note(self):
        """A bunch of wiki text with {warning} and {note}"""
        p = WikiParser()
        doc = pq(p.parse('\n\n{warning}\n\nthis is a warning\n\n{note}'
                         'this is a note{warning}!{/warning}{/note}'
                         "[[Installing Firefox]] '''internal''' ''link''"
                         '{/warning}\n\n'))
        eq_('!', doc('div.warning div.warning').text())
        eq_('this is a note !', doc('div.note').text())
        eq_('Installing Firefox', doc('a').text())
        eq_('internal', doc('strong').text())
        eq_('link', doc('em').text())

    def test_key_inline(self):
        """{key} stays inline"""
        p = WikiParser()
        doc = pq(p.parse('{key Cmd+Shift+Q}'))
        eq_(1, len(doc('p')))
        eq_(u'<span class="key">Cmd</span> + <span class="key">Shift</span>'
            u' + <span class="key">Q</span>', doc.html().replace('\n', ''))

    def test_template_inline(self):
        """Inline templates are not wrapped in <p>s"""
        doc, p = doc_parse_markup('<span class="key">{{{1}}}</span>',
                                  '[[T:test|Cmd]] + [[T:test|Shift]]')
        eq_(1, len(doc('p')))

    def test_template_multiline(self):
        """Multiline templates are wrapped in <p>s"""
        doc, p = doc_parse_markup('<span class="key">\n{{{1}}}</span>',
                                  '[[T:test|Cmd]]')
        eq_(3, len(doc('p')))

    def test_key_split_callback(self):
        """The _key_split regex callback does what it claims"""
        key_p = PATTERNS[2][0]
        # Multiple keys, with spaces
        eq_('<span class="key">ctrl</span> + <span class="key">alt</span> + '
            '<span class="key">del</span>',
            key_p.sub(_key_split, '{key ctrl + alt +   del}'))
        # Single key with spaces in it
        eq_('<span class="key">a key</span>',
            key_p.sub(_key_split, '{key a key}'))
        # Multiple keys with quotes and spaces
        eq_('<span class="key">"Param-One" and</span> + <span class="key">'
            'param</span> + <span class="key">two</span>',
            key_p.sub(_key_split, '{key  "Param-One" and + param+two}'))
        eq_('<span class="key">multi\nline</span> + '
            '<span class="key">me</span>',
            key_p.sub(_key_split, '{key multi\nline\n+me}'))

    def test_key_split_brace_callback(self):
        """Adding brace inside {key ...}"""
        key_p = PATTERNS[2][0]
        eq_('<span class="key">ctrl</span> + <span class="key">and</span> '
            'Here is }',
            key_p.sub(_key_split, '{key ctrl + and} Here is }'))
        eq_('<span class="key">ctrl</span> + <span class="key">and</span> + '
            '<span class="key">{</span>',
            key_p.sub(_key_split, '{key ctrl + and + {}'))

    def test_simple_inline_custom(self):
        """Simple custom inline syntax: menu, button, filepath, pref"""
        p = WikiParser()
        tags = ['menu', 'button', 'filepath', 'pref']
        for tag in tags:
            doc = pq(p.parse('{%s this is a %s}' % (tag, tag)))
            eq_('this is a ' + tag, doc('span.' + tag).text())

    def test_general_warning_note_inline_custom(self):
        """A mix of custom inline syntax with warnings and notes"""
        p = WikiParser()
        doc = pq(p.parse('\n\n{warning}\n\nthis is a {button warning}\n{note}'
                         'this is a {menu note}{warning}!{/warning}{/note}'
                         "'''{filepath internal}''' ''{menu hi!}''{/warning}"))
        eq_('warning', doc('div.warning span.button').text())
        eq_('this is a note !', doc('div.note').text())
        eq_('note', doc('div.warning div.note span.menu').text())
        eq_('internal', doc('strong span.filepath').text())
        eq_('hi!', doc('em span.menu').text())


class TestWikiTemplate(SkippedTestCase):
    fixtures = ['users.json']

    def test_template(self):
        """Simple template markup."""
        doc, _ = doc_parse_markup('Test content', '[[Template:test]]')
        eq_('Test content', doc.text())

    def test_template_does_not_exist(self):
        """Return a message if template does not exist"""
        p = WikiParser()
        doc = pq(p.parse('[[Template:test]]'))
        eq_('The template "test" does not exist or has no approved revision.',
            doc.text())

    def test_template_locale(self):
        """Localized template is returned."""
        py_doc, p = doc_parse_markup('English content', '[[Template:test]]')
        parent = document()
        d = document(parent=parent, title='Template:test', locale='fr')
        d.save()
        r = revision(content='French content', document=d, is_approved=True)
        r.save()
        eq_('English content', py_doc.text())
        py_doc = pq(p.parse('[[T:test]]', locale='fr'))
        eq_('French content', py_doc.text())

    def test_template_not_exist(self):
        """If template does not exist in set locale or English."""
        p = WikiParser()
        doc = pq(p.parse('[[T:test]]', locale='fr'))
        eq_('The template "test" does not exist or has no approved revision.',
            doc.text())

    def test_template_locale_fallback(self):
        """If localized template does not exist, fall back to English."""
        _, p = doc_parse_markup('English content', '[[Template:test]]')
        doc = pq(p.parse('[[T:test]]', locale='fr'))
        eq_('English content', doc.text())

    def test_template_anonymous_params(self):
        """Template markup with anonymous parameters."""
        doc, p = doc_parse_markup('{{{1}}}:{{{2}}}',
                                  '[[Template:test|one|two]]')
        eq_('one:two', doc.text())
        doc = pq(p.parse('[[T:test|two|one]]'))
        eq_('two:one', doc.text())

    def test_template_named_params(self):
        """Template markup with named parameters."""
        doc, p = doc_parse_markup('{{{a}}}:{{{b}}}',
                                  '[[Template:test|a=one|b=two]]')
        eq_('one:two', doc.text())
        doc = pq(p.parse('[[T:test|a=two|b=one]]'))
        eq_('two:one', doc.text())

    def test_template_numbered_params(self):
        """Template markup with numbered parameters."""
        doc, p = doc_parse_markup('{{{1}}}:{{{2}}}',
                                  '[[Template:test|2=one|1=two]]')
        eq_('two:one', doc.text())
        doc = pq(p.parse('[[T:test|2=two|1=one]]'))
        eq_('one:two', doc.text())

    def test_template_wiki_markup(self):
        """A template with wiki markup"""
        doc, _ = doc_parse_markup("{{{1}}}:{{{2}}}\n''wiki''\n'''markup'''",
                                  '[[Template:test|2=one|1=two]]')

        eq_('two:one', doc('p')[1].text.replace('\n', ''))
        eq_('wiki', doc('em')[0].text)
        eq_('markup', doc('strong')[0].text)

    def test_template_args_inline_wiki_markup(self):
        """Args that contain inline wiki markup are parsed"""
        doc, _ = doc_parse_markup('{{{1}}}\n\n{{{2}}}',
                                  "[[Template:test|'''one'''|''two'']]")

        eq_("<p/><p><strong>one</strong></p><p><em>two</em></p><p/>",
            doc.html().replace('\n', ''))

    def test_template_args_block_wiki_markup(self):
        """Args that contain block level wiki markup aren't parsed"""
        doc, _ = doc_parse_markup('{{{1}}}\n\n{{{2}}}',
                                  "[[Template:test|* ordered|# list]]")

        eq_("<p/><p>* ordered</p><p># list</p><p/>",
            doc.html().replace('\n', ''))

    def test_format_template_content_named(self):
        """_ftc handles named arguments"""
        eq_('ab', _ftc('{{{some}}}{{{content}}}',
                       {'some': 'a', 'content': 'b'}))

    def test_format_template_content_numbered(self):
        """_ftc handles numbered arguments"""
        eq_('a:b', _ftc('{{{1}}}:{{{2}}}', {'1': 'a', '2': 'b'}))

    def test_build_template_params_anonymous(self):
        """_btp handles anonymous arguments"""
        eq_({'1': '<span>a</span>', '2': 'test'},
            _btp(['<span>a</span>', 'test']))

    def test_build_template_params_numbered(self):
        """_btp handles numbered arguments"""
        eq_({'20': 'a', '10': 'test'}, _btp(['20=a', '10=test']))

    def test_build_template_params_named(self):
        """_btp handles only named-arguments"""
        eq_({'a': 'b', 'hi': 'test'}, _btp(['hi=test', 'a=b']))

    def test_build_template_params_named_anonymous(self):
        """_btp handles mixed named and anonymous arguments"""
        eq_({'1': 'a', 'hi': 'test'}, _btp(['hi=test', 'a']))

    def test_build_template_params_named_numbered(self):
        """_btp handles mixed named and numbered arguments"""
        eq_({'10': 'a', 'hi': 'test'}, _btp(['hi=test', '10=a']))

    def test_build_template_params_named_anonymous_numbered(self):
        """_btp handles mixed named, anonymous and numbered arguments"""
        eq_({'1': 'a', 'hi': 'test', '3': 'z'}, _btp(['hi=test', 'a', '3=z']))

    def test_unapproved_template(self):
        document(title='Template:new').save()
        p = WikiParser()
        doc = pq(p.parse('[[T:new]]'))
        eq_('The template "new" does not exist or has no approved revision.',
            doc.text())

    def test_for_in_template(self):
        """Verify that {for}'s render correctly in template."""
        d = document(title='Template:for')
        d.save()
        r = revision(document=d,
                     content='{for win}windows{/for}{for mac}mac{/for}')
        r.is_approved = True
        r.save()
        p = WikiParser()
        content = p.parse('[[Template:for]]')
        eq_('<p><span class="for" data-for="win">windows</span>'
            '<span class="for" data-for="mac">mac</span>\n\n</p>',
            content)

    def test_button_for_nesting(self):
        """You can nest {for}s inside {button}."""
        text = '{button start {for mac}mac{/for}{for win}win{/for} rest}'
        p = WikiParser()
        content = p.parse(text)
        eq_(u'<p><span class="button">start '
            u'<span class="for" data-for="mac">mac</span>'
            u'<span class="for" data-for="win">win</span> '
            u'rest</span>\n</p>', content)

    def test_button_image_for_nesting(self):
        """You can nest [[Image:]] inside {for} inside {button}."""
        image(title='image-file.png')
        text = '{button {for mac}[[Image:image-file.png]]{/for} text}'
        p = WikiParser()
        doc = pq(p.parse(text))
        eq_('frameless', doc('img').attr('class'))
        eq_(0, doc('div.caption').length)
        eq_(0, doc('div.img').length)

    def test_direct_recursion(self):
        """Make sure direct recursion is caught on the very first nesting."""
        d = document(title='Template:Boo')
        d.save()

        # Twice so the second revision sees content identical to itself:
        for i in range(2):
            revision(document=d, content='Fine [[Template:Boo]] Fellows',
                     is_approved=True).save()

        eq_('<p>Fine %s Fellows\n</p>' % (RECURSION_MESSAGE % 'Template:Boo'),
            d.content_parsed)

    def test_indirect_recursion(self):
        """Make sure indirect recursion is caught."""
        boo = document(title='Template:Boo')
        boo.save()
        yah = document(title='Template:Yah')
        yah.save()
        revision(document=boo, content='Paper [[Template:Yah]] Cups',
                 is_approved=True).save()
        revision(document=yah, content='Wooden [[Template:Boo]] Bats',
                 is_approved=True).save()
        recursion_message = RECURSION_MESSAGE % 'Template:Boo'
        eq_('<p>Paper Wooden %s Bats\n Cups\n</p>' % recursion_message,
            boo.content_parsed)


class TestWikiInclude(SkippedTestCase):
    fixtures = ['users.json']

    def test_revision_include(self):
        """Simple include markup."""
        _, _, p = doc_rev_parser('Test content', 'Test title')

        # Existing title returns document's content
        doc = pq(p.parse('[[I:Test title]]'))
        eq_('Test content', doc.text())

        # Nonexisting title returns 'Document not found'
        doc = pq(p.parse('[[Include:Another title]]'))
        eq_('The document "Another title" does not exist.', doc.text())

    def test_revision_include_locale(self):
        """Include finds document in the correct locale."""
        _, _, p = doc_rev_parser('English content', 'Test title')
        # Parsing in English should find the French article
        doc = pq(p.parse('[[Include:Test title]]', locale='en-US'))
        eq_('English content', doc.text())
        # The French article will include the English content as fallback.
        doc = pq(p.parse('[[I:Test title]]', locale='fr'))
        eq_('English content', doc.text())
        # Create the French article, and test again
        parent_rev = revision()
        d = document(parent=parent_rev.document, title='Test title',
                     locale='fr')
        d.save()
        r = revision(document=d, content='French content', is_approved=True)
        r.save()
        # Parsing in French should find the French article
        doc = pq(p.parse('[[Include:Test title]]', locale='fr'))
        eq_('French content', doc.text())

    def test_direct_recursion(self):
        """Make sure direct recursion is caught on the very first nesting."""
        d = document(title='Boo')
        d.save()

        # Twice so the second revision sees content identical to itself:
        for i in range(2):
            revision(document=d, content='Fine [[Include:Boo]] Fellows',
                     is_approved=True).save()

        eq_('<p>Fine %s Fellows\n</p>' % (RECURSION_MESSAGE % 'Boo'),
            d.content_parsed)

    def test_indirect_recursion(self):
        """Make sure indirect recursion is caught."""
        boo = document(title='Boo')
        boo.save()
        yah = document(title='Yah')
        yah.save()
        revision(document=boo, content='Paper [[Include:Yah]] Cups',
                 is_approved=True).save()
        revision(document=yah, content='Wooden [[Include:Boo]] Bats',
                 is_approved=True).save()
        recursion_message = RECURSION_MESSAGE % 'Boo'

        # boo.content_parsed is something like <p>Paper </p><p>Wooden
        # [Recursive inclusion of "Boo"] Bats\n</p> Cups\n<p></p>.
        eq_('Paper Wooden %s Bats Cups' % recursion_message,
            boo.content_parsed.replace('</p>', '').replace('<p>',
            '').replace('\n', ''))


class TestWikiVideo(SkippedTestCase):
    """Video hook."""
    fixtures = ['users.json']

    def tearDown(self):
        Video.objects.all().delete()
        super(TestWikiVideo, self).tearDown()

    def test_video_english(self):
        """Video is created and found in English."""
        v = video()
        d, _, p = doc_rev_parser('[[V:Some title]]')
        doc = pq(d.html)
        eq_('video', doc('div.video').attr('class'))
        eq_(u'<source src="{0}" '
            u'type="video/webm"><source src="{1}" type="video/ogg"/>'
            u'</source>'.format(v.webm.url, v.ogv.url),
            doc('video').html())
        eq_(1, len(doc('video')))
        eq_(2, len(doc('source')))
        data_fallback = doc('video').attr('data-fallback')
        eq_(v.flv.url, data_fallback)

    def test_video_fallback_french(self):
        """English video is found in French."""
        p = WikiParser()
        self.test_video_english()
        doc = pq(p.parse('[[V:Some title]]', locale='fr'))
        eq_('video', doc('div.video').attr('class'))
        eq_(1, len(doc('video')))
        eq_(2, len(doc('source')))
        data_fallback = doc('video').attr('data-fallback')
        eq_(Video.objects.all()[0].flv.url, data_fallback)

    def test_video_not_exist(self):
        """Video does not exist."""
        p = WikiParser()
        doc = pq(p.parse('[[V:Some title]]', locale='fr'))
        eq_('The video "Some title" does not exist.', doc.text())

    def test_video_modal(self):
        """Video modal defaults for plcaeholder and text."""
        v = video()
        replacement = ('<img class="video-thumbnail" src="%s"/>' %
                       v.thumbnail_url_if_set())
        d, _, p = doc_rev_parser(
            '[[V:Some title|modal]]')
        doc = pq(d.html)
        eq_('Some title', doc('.video-modal')[0].attrib['title'])
        eq_(1, doc('.video video').length)
        eq_(replacement, doc('.video-placeholder').html().strip())
        eq_('video modal-trigger', doc('div.video').attr('class'))

    def test_video_modal_caption_text(self):
        """Video modal can change title and placeholder text."""
        video()
        d, _, p = doc_rev_parser(
            '[[V:Some title|modal|placeholder=Place<b>holder</b>|title=WOOT]]')
        doc = pq(d.html)
        eq_('WOOT', doc('.video-modal')[0].attrib['title'])
        eq_('Place<b>holder</b>', doc('.video-placeholder').html().strip())

    def test_video_cdn(self):
        """Video URLs can link to the CDN if a CDN setting is set."""
        video()
        cdn_url = 'http://videos.mozilla.org/serv/sumo/'

        self.old_settings = deepcopy(settings._wrapped.__dict__)
        settings.GALLERY_VIDEO_URL = cdn_url
        d, _, p = doc_rev_parser('[[V:Some title]]')
        settings._wrapped.__dict__ = self.old_settings

        doc = pq(d.html)
        assert cdn_url in doc('video').attr('data-fallback')
        assert cdn_url in doc('source').eq(0).attr('src')
        assert cdn_url in doc('source').eq(1).attr('src')


def parsed_eq(want, to_parse):
    p = WikiParser()
    eq_(want, p.parse(to_parse).strip().replace('\n', ''))


class ForWikiTests(SkippedTestCase):
    """Tests for the wiki implementation of the {for} directive, which
    arranges for certain parts of the page to show only when viewed on certain
    OSes or browser versions"""

    def test_block(self):
        """A {for} set off by itself or wrapping a block-level element should
        be a paragraph or other kind of block-level thing."""
        parsed_eq('<p>Joe</p><p><span class="for">Red</span></p>'
                  '<p>Blow</p>',
                  'Joe\n\n{for}Red{/for}\n\nBlow')
        parsed_eq('<p>Joe</p><div class="for"><ul><li> Red</li></ul></div>'
                  '<p>Blow</p>',
                  'Joe\n\n{for}\n* Red\n{/for}\n\nBlow')

    def test_inline(self):
        """A for not meeting the conditions in test_block should be inline.
        """
        parsed_eq('<p>Joe</p>'
                  '<p>Red <span class="for">riding</span> hood</p>'
                  '<p>Blow</p>',

                  'Joe\n\nRed {for}riding{/for} hood\n\nBlow')

    def test_nested(self):
        """{for} tags should be nestable."""
        parsed_eq('<div class="for" data-for="mac"><p>Joe</p>'
                  '<p>Red <span class="for"><span class="for">riding'
                      '</span> hood</span></p>'
                  '<p>Blow</p></div>',

                  '{for mac}\n'
                  'Joe\n'
                  '\n'
                  'Red {for}{for}riding\n'
                  '{/for} hood{/for}\n'
                  '\n'
                  'Blow\n'
                  '{/for}')

    def test_data_attrs(self):
        """Make sure the correct attributes are set on the for element."""
        parsed_eq('<p><span class="for" data-for="mac,linux,3.6">'
                  'One</span></p>',
                  '{for mac,linux,3.6}One{/for}')

    def test_early_close(self):
        """Make sure the parser closes the for tag at the right place when
        its closer is early."""
        parsed_eq('<div class="for"><p>One</p>'
                  '<ul><li>Fish</li></ul></div>',
                  '{for}\nOne\n\n*Fish{/for}')

    def test_late_close(self):
        """If the closing for tag is not closed by the time the enclosing
        element of the opening for tag is closed, close the for tag
        just before the enclosing element."""
        parsed_eq(
            '<ul><li><span class="for">One</span></li>'
            '<li>Fish</li></ul><p>Two</p>',
            '*{for}One\n*Fish\n\nTwo\n{/for}')

    def test_missing_close(self):
        """If the closing for tag is missing, close the for tag just
        before the enclosing element."""
        parsed_eq(
            '<p><span class="for">One fish</span></p><p>Two fish</p>',
            '{for}One fish\n\nTwo fish')

    def test_unicode(self):
        """Make sure non-ASCII chars survive being wrapped in a for."""
        french = u'Vous parl\u00e9 Fran\u00e7ais'
        parsed_eq('<p><span class="for">' + french + '</span></p>',
                  '{for}' + french + '{/for}')

    def test_boolean_attr(self):
        """Make sure empty attributes don't raise exceptions."""
        parsed_eq('<p><video controls height="120">'
                    '<source src="/some/path/file.ogv" type="video/ogv">'
                  '</video></p>',
                  '<p><video controls="" height="120">'
                    '<source src="/some/path/file.ogv" type="video/ogv">'
                  '</video></p>')

    def test_adjacent_blocks(self):
        """Make sure one block-level {for} doesn't absorb an adjacent one."""
        p = WikiParser()
        html = p.parse('{for fx4}\n'
                       '{for mac}Fx4{/for}\n'
                       '{/for}\n'
                       '{for fx3}\n'
                       '{for mac}Fx3{/for}\n'
                       '{/for}')
        # The two div.fors should be siblings, not nested:
        eq_([], pq(html)('div.for div.for'))

    def test_leading_newlines(self):
        """Make sure leading newlines don't cause a block-level {for} to be
        sucked into the leading blank paragraph, causing the actual text to
        always be shown."""
        doc = pq(WikiParser().parse('\n\n{for linux}\nunixify\n{/for}'))
        eq_('unixify', doc('.for').text().strip())

    def test_big_swath(self):
        """Enclose a big section containing many tags."""
        parsed_eq('<div class="for"><h1 id="w_h1">H1</h1>'
                  '<h2 id="w_h2">H2</h2><p>Llamas are fun:</p>'
                  '<ul><li>Jumping</li><li>Rolling</li><li>Grazing</li></ul>'
                  '<p>They have high melting points.</p></div>',

                  '{for}\n'
                  '=H1=\n'
                  '==H2==\n'
                  'Llamas are fun:\n'
                  '\n'
                  '*Jumping\n'
                  '*Rolling\n'
                  '*Grazing\n'
                  '\n'
                  'They have high melting points.\n'
                  '{/for}')

    def test_block_level_section(self):
        """Make sure we recognize <section> as a block element."""
        p = WikiParser()
        html = p.parse('{for}<section>hi</section>{/for}')
        assert '<div' in html, "Didn't detect <section> tag as block level"


def balanced_eq(want, to_balance):
    """Run `to_balance` through the expander to get its tags balanced, and
    assert the result is `want`."""
    expander = ForParser(to_balance)
    eq_(want, expander.to_unicode())


def expanded_eq(want, to_expand):
    """Balance and expand the fors in `to_expand`, and assert equality with
    `want`."""
    expander = ForParser(to_expand)
    expander.expand_fors()
    eq_(want, expander.to_unicode())


def strip_eq(want, text):
    eq_(want, ForParser.strip_fors(text)[0])


class ForParserTests(SkippedTestCase):
    """Tests for the ForParser

    These are unit tests for ForParser, and ForWikiTests are
    (as a bonus) integration tests for it.

    """

    def test_well_formed(self):
        """Make sure the expander works on well-formed fragments."""
        html = '<ul><li type="1"><br><for>One</for></li></ul>'
        balanced_eq(html, html)

    def test_document_mode(self):
        """Make sure text chunks interspersed with tags are parsed right."""
        html = '<p>Hello<br>there, <br>you.</p>'
        balanced_eq(html, html)

    def test_early_close(self):
        """Make sure the parser closes the for tag at the right place when
        its closer is early."""
        balanced_eq('<div><for><p>One</p></for></div>',
                    '<div><for><p>One</for></for></p></div>')

    def test_late_close(self):
        """If the closing for tag is not closed by the time the enclosing
        element of the opening for tag is closed, close the for tag
        just before the enclosing element."""
        balanced_eq(
            '<ul><li><for><for>One</for></for></li></ul>',
            '<ul><li><for><for>One</li></ul></for>')

    def test_close_absent_at_end(self):
        """Make sure the parser closes for tags left open at the EOF.

        This mattered more when we weren't building a parse tree.

        """
        balanced_eq('<for><p>One</p></for>',
                    '<for><p>One</for></for></p>')

    def test_unicode(self):
        """Make sure this all works with non-ASCII chars."""
        html = u'<for>Vous parl\u00e9 Fran\u00e7ais</for>'
        balanced_eq(html, html)

    def test_div(self):
        """Make sure we use divs for fors containing block elements."""
        expanded_eq('<div class="for"><p>One</p></div>',
                    '<for><p>One</p></for>')

    def test_span(self):
        """Make sure we use spans for fors containing no block elements."""
        expanded_eq('<span class="for"><em>One</em></span>',
                    '<for><em>One</em></for>')

    def test_data_attrs(self):
        """Make sure the data- attributes look good."""
        expanded_eq('<span class="for" data-for="mac,linux">One</span>',
                    '<for data-for="mac,linux">One</for>')

    def test_on_own_line(self):
        def on_own_line_eq(want, text):
            """Assert that on_own_line operates as expected on the first match
            in `text`."""
            match = ForParser._FOR_OR_CLOSER.search(text)
            eq_(want, ForParser._on_own_line(match, match.groups(3)))
        on_own_line_eq((True, True, True), '{for}')
        on_own_line_eq((True, True, True), '{for} ')
        on_own_line_eq((False, False, True), ' {for}')
        on_own_line_eq((True, False, True), 'q\n{for}')
        on_own_line_eq((False, True, False), '{for}q')
        on_own_line_eq((True, False, False), '\n{for} \nq')

    def test_strip(self):
        strip_eq('\x070\x07inline\x07/sf\x07', '{for}inline{/for}')
        strip_eq('\x070\x07\n\nblock\n\n\x07/sf\x07',
                 '{for}\nblock\n{/for}')
        strip_eq('\x070\x07inline\n\n\x07/sf\x07',
                 '{for}inline\n{/for}')
        strip_eq('\x070\x07\n\nblock\x07/sf\x07', '{for}\nblock{/for}')

    def test_whitespace_lookbehind(self):
        """Assert strip_fors is aware of newlines preceding the current match.

        This used to fail because both the postspace for the first closer and
        the prespace for the 2nd got 1 \n added, resulting in 3, which is 1
        too many. Now we use the preceding_whitespace function to look behind
        and take preceding newlines into account.

        """
        strip_eq('\x070\x07\n\n\x071\x07inline\x07/sf\x07\n\n\x07/sf\x07',
                 '{for}\n{for}inline{/for}\n{/for}')

    def test_matches_see_replacements(self):
        """Make sure each whitespace lookbehind takes into account the effect
        of previous replacements' whitespace additions.

        When this bug existed, strip_fors would add a \n for postspace to the
        2nd {/for}, but then the preceding_whitespace call for the next {for}
        wouldn't see what was added, since it was still looking in the
        original string, without the replacements applied.

        """
        strip_eq('\x070\x07\n\n\x071\x07Fx4\x07/sf\x07\n\n\x07/sf\x07\n\n'
                 '\x072\x07\n\n\x073\x07Fx3\x07/sf\x07\n\n\x07/sf\x07',
                 '{for fx4}\n'
                 '{for mac}Fx4{/for}\n'
                 '{/for}\n'
                 '{for fx3}\n'
                 '{for mac}Fx3{/for}\n'
                 '{/for}')

    def test_self_closers(self):
        """Make sure self-closing tags aren't balanced as paired ones."""
        balanced_eq('<img src="smoo"><span>g</span>',
                    '<img src="smoo"><span>g</span>')
        balanced_eq('<img src="smoo"><span>g</span>',
                    '<img src="smoo"/><span>g</span>')

    def test_leading_text_nodes(self):
        """Make sure the parser handles a leading naked run of text.

        Test inner runs of text while we're at it.

        """
        html = 'A<i>hi</i>B<i>there</i>C'
        p = ForParser(html)
        eq_(html, p.to_unicode())
