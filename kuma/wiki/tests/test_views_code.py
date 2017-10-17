from waffle.models import Switch
import pytest

from kuma.attachments.models import Attachment
from kuma.attachments.tests import make_test_file
from kuma.core.urlresolvers import reverse
from kuma.wiki.models import Revision

from . import normalize_html


@pytest.fixture
def code_sample_doc(root_doc, wiki_user):
    sample_page = """
        <p>This is a page. Deal with it.</p>
        <div id="sample1" class="code-sample">
            <pre class="brush: html">Some HTML</pre>
            <pre class="brush: css">.some-css { color: red; }</pre>
            <pre class="brush: js">window.alert("HI THERE")</pre>
        </div>
        <p>test</p>
        {{ EmbedLiveSample('sample1') }}
    """
    root_doc.current_revision = Revision.objects.create(
        document=root_doc, creator=wiki_user, content=sample_page)
    root_doc.save()
    return root_doc


class ConstanceConfigWrapper(object):
    """A Constance configuration wrapper to allow overriding the config."""
    _original_values = []

    def __setattr__(self, attr, value):
        from constance import config
        self._original_values.append((attr, getattr(config, attr)))
        setattr(config, attr, value)
        # This can fail if Constance uses a cached database backend
        # CONSTANCE_DATABASE_CACHE_BACKEND = False to disable
        assert getattr(config, attr) == value

    def finalize(self):
        from constance import config
        for attr, value in reversed(self._original_values):
            setattr(config, attr, value)
        del self._original_values[:]


@pytest.fixture
def constance_config(db, settings):
    """A Constance config object which restores changes after the testrun."""
    wrapper = ConstanceConfigWrapper()
    yield wrapper
    wrapper.finalize()


def test_code_sample(code_sample_doc, constance_config, client, settings):
    """The raw source for a document can be requested."""
    Switch.objects.create(name='application_ACAO', active=True)
    url = reverse('wiki.code_sample', locale='en-US',
                  args=[code_sample_doc.slug, 'sample1'])
    constance_config.KUMA_WIKI_IFRAME_ALLOWED_HOSTS = '^.*testserver'
    response = client.get(url, HTTP_HOST='testserver')
    assert response.status_code == 200
    assert response['Access-Control-Allow-Origin'] == '*'
    assert not response.has_header('Vary')
    assert response.content.startswith('<!DOCTYPE html>')

    normalized = normalize_html(response.content)
    expected = (
        '<link href="%sbuild/styles/samples.css"'
        ' rel="stylesheet" type="text/css">'
        '<style type="text/css">.some-css { color: red; }</style>'
        'Some HTML'
        '<script type="text/javascript">window.alert("HI THERE")</script>'
        % settings.STATIC_URL)
    assert normalized == expected


def test_code_sample_host_restriction(code_sample_doc, constance_config,
                                      client):
    """Users are not allowed to view samples on a restricted domain."""
    url = reverse('wiki.code_sample', locale='en-US',
                  args=[code_sample_doc.slug, 'sample1'])
    constance_config.KUMA_WIKI_IFRAME_ALLOWED_HOSTS = '^.*sampleserver'
    response = client.get(url, HTTP_HOST='testserver')
    assert response.status_code == 403
    response = client.get(url, HTTP_HOST='sampleserver')
    assert response.status_code == 200


def test_raw_code_sample_file(code_sample_doc, constance_config,
                              wiki_user, admin_client):

    # Upload an attachment
    upload_url = reverse('attachments.edit_attachment', locale='en-US',
                         kwargs={'document_path': code_sample_doc.slug})
    file_for_upload = make_test_file(content='Something something unique')
    post_data = {
        'title': 'An uploaded file',
        'description': 'A unique experience for your file serving needs.',
        'comment': 'Yadda yadda yadda',
        'file': file_for_upload,
    }
    constance_config.KUMA_WIKI_IFRAME_ALLOWED_HOSTS = '^.*testserver'
    constance_config.WIKI_ATTACHMENT_ALLOWED_TYPES = 'text/plain'
    response = admin_client.post(upload_url, data=post_data)
    assert response.status_code == 302
    edit_url = reverse('wiki.edit', locale='en-US',
                       args=(code_sample_doc.slug,))
    assert response.url == 'http://testserver' + edit_url

    # Add a relative reference to the sample content
    attachment = Attachment.objects.get(title='An uploaded file')
    filename = attachment.current_revision.filename
    url_css = 'url("files/%(attachment_id)s/%(filename)s")' % {
        'attachment_id': attachment.id,
        'filename': filename,
    }
    new_content = code_sample_doc.current_revision.content.replace(
        'color: red', url_css)
    code_sample_doc.current_revision = Revision.objects.create(
        document=code_sample_doc, creator=wiki_user, content=new_content)
    code_sample_doc.save()

    # URL is in the sample
    sample_url = reverse('wiki.code_sample', locale='en-US',
                         args=[code_sample_doc.slug, 'sample1'])

    response = admin_client.get(sample_url)
    assert response.status_code == 200
    assert url_css in response.content

    # Getting the URL redirects to the attachment
    file_url = reverse('wiki.raw_code_sample_file', locale='en-US',
                       args=(code_sample_doc.slug, 'sample1', attachment.id,
                             filename))
    response = admin_client.get(file_url)
    assert response.status_code == 302
    assert response.url == attachment.get_file_url()
    assert not response.has_header('Vary')
