import pytest
from waffle.testutils import override_switch

from kuma.attachments.models import Attachment
from kuma.attachments.tests import make_test_file
from kuma.core.urlresolvers import reverse

from . import normalize_html
from ..models import Revision


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


@pytest.mark.parametrize('domain', ('HOST', 'ORIGIN'))
def test_code_sample(code_sample_doc, client, settings, domain):
    """The raw source for a document can be requested."""
    url = reverse('wiki.code_sample',
                  args=[code_sample_doc.slug, 'sample1'])
    setattr(settings, 'ATTACHMENT_' + domain, 'testserver')
    with override_switch('application_ACAO', True):
        response = client.get(
            url,
            HTTP_HOST='testserver',
            HTTP_IF_NONE_MATCH='"some-old-etag"'
        )
    assert response.status_code == 200
    assert response['Access-Control-Allow-Origin'] == '*'
    assert 'Last-Modified' not in response
    assert 'ETag' in response
    assert 'public' in response['Cache-Control']
    assert 'max-age=86400' in response['Cache-Control']
    assert response.content.startswith(b'<!DOCTYPE html>')

    normalized = normalize_html(response.content)
    expected = (
        '<meta charset="utf-8">'
        '<link href="%sbuild/styles/samples.css"'
        ' rel="stylesheet" type="text/css">'
        '<style type="text/css">.some-css { color: red; }</style>'
        '<title>Root Document - sample1 - code sample</title>'
        'Some HTML'
        '<script>window.alert("HI THERE")</script>'
        % settings.STATIC_URL)
    assert normalized == expected


def test_code_sample_host_not_allowed(code_sample_doc, settings, client):
    """Users are not allowed to view samples on a restricted domain."""
    url = reverse('wiki.code_sample',
                  args=[code_sample_doc.slug, 'sample1'])
    host = 'testserver'
    assert settings.ATTACHMENT_HOST != host
    assert settings.ATTACHMENT_ORIGIN != host
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 403


def test_code_sample_host_allowed(code_sample_doc, settings, client):
    """Users are allowed to view samples on an allowed domain."""
    host = 'sampleserver'
    url = reverse('wiki.code_sample',
                  args=[code_sample_doc.slug, 'sample1'])
    settings.ATTACHMENT_HOST = host
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 'max-age=86400' in response['Cache-Control']


def test_code_sample_host_restricted_host(code_sample_doc, constance_config,
                                          settings, client):
    """Users are allowed to view samples on the attachment domain."""
    url = reverse('wiki.code_sample',
                  args=[code_sample_doc.slug, 'sample1'])
    host = 'sampleserver'
    settings.ALLOWED_HOSTS.append(host)
    settings.ATTACHMENT_HOST = host
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    # Setting the KUMASCRIPT_TIMEOUT to a non-zero value forces kumascript
    # rendering so we ensure that path is tested for these requests that use
    # a restricted urlconf environment.
    constance_config.KUMASCRIPT_TIMEOUT = 1
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert 'public' in response['Cache-Control']
    assert 'max-age=86400' in response['Cache-Control']


def test_raw_code_sample_file(code_sample_doc, constance_config,
                              wiki_user, admin_client, settings):

    # Upload an attachment
    upload_url = reverse('attachments.edit_attachment',
                         kwargs={'document_path': code_sample_doc.slug})
    file_for_upload = make_test_file(content='Something something unique')
    post_data = {
        'title': 'An uploaded file',
        'description': 'A unique experience for your file serving needs.',
        'comment': 'Yadda yadda yadda',
        'file': file_for_upload,
    }
    constance_config.WIKI_ATTACHMENT_ALLOWED_TYPES = 'text/plain'
    response = admin_client.post(upload_url, data=post_data,
                                 HTTP_HOST=settings.WIKI_HOST)
    assert response.status_code == 302
    edit_url = reverse('wiki.edit', args=(code_sample_doc.slug,))
    assert response.url == edit_url

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
    sample_url = reverse('wiki.code_sample',
                         args=[code_sample_doc.slug, 'sample1'])

    settings.ATTACHMENT_HOST = 'testserver'
    response = admin_client.get(sample_url)
    assert response.status_code == 200
    assert url_css.encode('utf-8') in response.content
    assert 'public' in response['Cache-Control']
    assert 'max-age=86400' in response['Cache-Control']

    # Getting the URL redirects to the attachment
    file_url = reverse('wiki.raw_code_sample_file',
                       args=(code_sample_doc.slug, 'sample1', attachment.id,
                             filename))
    response = admin_client.get(file_url)
    assert response.status_code == 302
    assert response.url == attachment.get_file_url()
    assert not response.has_header('Vary')
    assert 'Cache-Control' in response
    assert 'public' in response['Cache-Control']
    assert 'max-age=432000' in response['Cache-Control']
