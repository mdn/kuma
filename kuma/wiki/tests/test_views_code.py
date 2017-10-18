from constance.test import override_config
from django.conf import settings
from django.test.utils import override_settings
from pyquery import PyQuery as pq
from waffle.models import Switch

from kuma.attachments.models import Attachment
from kuma.attachments.tests import make_test_file
from kuma.core.tests import eq_, ok_
from kuma.core.urlresolvers import reverse
from kuma.users.tests import UserTestCase

from . import WikiTestCase, document, normalize_html, revision


class CodeSampleViewTests(UserTestCase, WikiTestCase):
    localizing_client = True

    @override_config(
        KUMA_WIKI_IFRAME_ALLOWED_HOSTS='^https?\:\/\/testserver')
    def test_code_sample_1(self):
        """The raw source for a document can be requested"""
        rev = revision(is_approved=True, save=True, content="""
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <p>test</p>
            {{ EmbedLiveSample('sample1') }}
        """)
        expecteds = (
            '<style type="text/css">.some-css { color: red; }</style>',
            'Some HTML',
            '<script type="text/javascript">window.alert("HI THERE")</script>',
        )

        Switch.objects.create(name='application_ACAO', active=True)
        response = self.client.get(reverse('wiki.code_sample',
                                           args=[rev.document.slug, 'sample1']),
                                   HTTP_HOST='testserver')
        ok_('Access-Control-Allow-Origin' in response)
        eq_('*', response['Access-Control-Allow-Origin'])
        eq_(200, response.status_code)
        normalized = normalize_html(response.content)

        # Content checks
        ok_('<!DOCTYPE html>' in response.content)
        for item in expecteds:
            ok_(item in normalized)

    @override_config(
        KUMA_WIKI_IFRAME_ALLOWED_HOSTS='^https?\:\/\/sampleserver')
    def test_code_sample_host_restriction(self):
        rev = revision(is_approved=True, save=True, content="""
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <p>test</p>
        """)

        response = self.client.get(reverse('wiki.code_sample',
                                           args=[rev.document.slug,
                                                 'sample1']),
                                   HTTP_HOST='testserver')
        eq_(403, response.status_code)

        response = self.client.get(reverse('wiki.code_sample',
                                           args=[rev.document.slug,
                                                 'sample1']),
                                   HTTP_HOST='sampleserver')
        eq_(200, response.status_code)

    @override_config(
        KUMA_WIKI_IFRAME_ALLOWED_HOSTS='^https?\:\/\/sampleserver')
    def test_code_sample_iframe_embed(self):
        slug = 'test-code-embed'
        embed_url = ('https://sampleserver/%s/docs/%s$samples/sample1' %
                     (settings.WIKI_DEFAULT_LANGUAGE, slug))

        doc_src = """
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { color: red; }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <iframe id="if1" src="%(embed_url)s"></iframe>
            <iframe id="if2" src="http://testserver"></iframe>
            <iframe id="if3" src="https://some.alien.site.com"></iframe>
            <p>test</p>
        """ % dict(embed_url=embed_url)

        slug = 'test-code-doc'
        rev = revision(is_approved=True, save=True)
        revision(save=True, document=rev.document,
                 title="Test code doc", slug=slug,
                 content=doc_src)

        response = self.client.get(reverse('wiki.document',
                                           args=(rev.document.slug,)))
        eq_(200, response.status_code)

        page = pq(response.content)

        if1 = page.find('#if1')
        eq_(if1.length, 1)
        eq_(if1.attr('src'), embed_url)

        if2 = page.find('#if2')
        eq_(if2.length, 1)
        eq_(if2.attr('src'), '')

        if3 = page.find('#if3')
        eq_(if3.length, 1)
        eq_(if3.attr('src'), '')


class CodeSampleViewFileServingTests(UserTestCase, WikiTestCase):

    @override_config(
        KUMA_WIKI_IFRAME_ALLOWED_HOSTS='^https?\:\/\/testserver',
        WIKI_ATTACHMENT_ALLOWED_TYPES='text/plain')
    @override_settings(ATTACHMENT_HOST='testserver')
    def test_code_sample_file_serving(self):
        doc = document(locale='en-US', save=True)
        self.client.login(username='admin', password='testpass')
        # first let's upload a file
        file_for_upload = make_test_file(content='Something something unique')
        post_data = {
            'title': 'An uploaded file',
            'description': 'A unique experience for your file serving needs.',
            'comment': 'Yadda yadda yadda',
            'file': file_for_upload,
        }
        response = self.client.post(reverse('attachments.edit_attachment',
                                            kwargs={'document_path': doc.slug},
                                            locale='en-US'),
                                    data=post_data)
        eq_(response.status_code, 302)

        # then build the document and revision we need to test
        attachment = Attachment.objects.get(title='An uploaded file')
        filename = attachment.current_revision.filename
        url_css = 'url("files/%(attachment_id)s/%(filename)s")' % {
            'attachment_id': attachment.id,
            'filename': filename,
        }
        rev = revision(is_approved=True, save=True, content="""
            <p>This is a page. Deal with it.</p>
            <div id="sample1" class="code-sample">
                <pre class="brush: html">Some HTML</pre>
                <pre class="brush: css">.some-css { background: %s }</pre>
                <pre class="brush: js">window.alert("HI THERE")</pre>
            </div>
            <p>test</p>
        """ % url_css)

        # then see of the code sample view has successfully found the sample
        response = self.client.get(reverse('wiki.code_sample',
                                           args=[rev.document.slug, 'sample1'],
                                           locale='en-US'))
        eq_(response.status_code, 200)
        normalized = normalize_html(response.content)
        ok_(url_css in normalized)

        # and then we try if a redirect by the file serving view redirects
        # to the main file serving view
        response = self.client.get(reverse('wiki.raw_code_sample_file',
                                           args=[rev.document.slug,
                                                 'sample1',
                                                 attachment.id,
                                                 filename],
                                           locale='en-US'))
        eq_(response.status_code, 302)
        eq_(response['Location'], attachment.get_file_url())
