from datetime import datetime

import pytest
from django.core.files.base import ContentFile
from pyquery import PyQuery as pq

from kuma.attachments.models import Attachment, AttachmentRevision
from kuma.core.urlresolvers import reverse

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
        document=root_doc, creator=wiki_user, content=sample_page
    )
    root_doc.save()
    return root_doc


@pytest.fixture
def attachment(db, wiki_user):
    title = "Test text file"
    result = Attachment(title=title)
    result.save()
    revision = AttachmentRevision(
        title=title,
        is_approved=True,
        attachment=result,
        mime_type="text/plain",
        description="Initial upload",
        created=datetime.now(),
    )
    revision.creator = wiki_user
    revision.file.save("test.txt", ContentFile(b"This is only a test."))
    revision.make_current()
    return result


@pytest.mark.parametrize("domain", ("HOST", "ORIGIN"))
def test_code_sample(code_sample_doc, client, settings, domain):
    """The raw source for a document can be requested."""
    url = reverse("wiki.code_sample", args=[code_sample_doc.slug, "sample1"])
    setattr(settings, "ATTACHMENT_" + domain, "testserver")
    response = client.get(
        url, HTTP_HOST="testserver", HTTP_IF_NONE_MATCH='"some-old-etag"'
    )
    assert response.status_code == 200
    assert response["Access-Control-Allow-Origin"] == "*"
    assert "Last-Modified" not in response
    assert "ETag" in response
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]
    assert response.content.startswith(b"<!DOCTYPE html>")

    doc = pq(response.content)
    assert len(doc.find("style")) == 2
    assert ".playable-code" in doc.find("style").eq(0).text()
    assert doc.find("style").eq(1).text() == ".some-css { color: red; }"
    assert "Some HTML" in doc.find("body").text()
    assert doc.find("script").text() == 'window.alert("HI THERE")'
    assert doc.find("title").text() == "Root Document - sample1 - code sample"


@pytest.mark.parametrize("host", ("dev.moz.org", "x.dev.moz.org", "x.y.dev.moz.org"))
def test_code_sample_host_not_allowed(code_sample_doc, settings, client, host):
    """Users are not allowed to view samples on a restricted domain."""
    url = reverse("wiki.code_sample", args=[code_sample_doc.slug, "sample1"])
    settings.DOMAIN = "dev.moz.org"
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 403


def test_code_sample_host_allowed(code_sample_doc, settings, client):
    """Users are allowed to view samples on an allowed domain."""
    host = "sampleserver"
    url = reverse("wiki.code_sample", args=[code_sample_doc.slug, "sample1"])
    settings.ATTACHMENT_HOST = host
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]


def test_code_sample_host_restricted_host(code_sample_doc, settings, client):
    """Users are allowed to view samples on the attachment domain."""
    url = reverse("wiki.code_sample", args=[code_sample_doc.slug, "sample1"])
    host = "sampleserver"
    settings.ALLOWED_HOSTS.append(host)
    settings.ATTACHMENT_HOST = host
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]


def test_raw_code_sample_file(
    attachment, code_sample_doc, wiki_user, admin_client, settings
):
    filename = attachment.current_revision.filename
    url_css = f'url("files/{attachment.id}/{filename}")'
    new_content = code_sample_doc.current_revision.content.replace(
        "color: red", url_css
    )
    code_sample_doc.current_revision = Revision.objects.create(
        document=code_sample_doc, creator=wiki_user, content=new_content
    )
    code_sample_doc.save()

    # URL is in the sample
    sample_url = reverse("wiki.code_sample", args=[code_sample_doc.slug, "sample1"])

    settings.ATTACHMENT_HOST = "testserver"
    response = admin_client.get(sample_url)
    assert response.status_code == 200
    assert url_css.encode() in response.content
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]

    # Getting the URL redirects to the attachment
    file_url = reverse(
        "wiki.raw_code_sample_file",
        args=(code_sample_doc.slug, "sample1", attachment.id, filename),
    )
    response = admin_client.get(file_url)
    assert response.status_code == 302
    assert response.url == attachment.get_file_url()
    assert not response.has_header("Vary")
    assert "Cache-Control" in response
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]
