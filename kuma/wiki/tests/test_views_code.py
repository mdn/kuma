from datetime import datetime

import pytest

from django.core.files.base import ContentFile

from kuma.attachments.models import Attachment, AttachmentRevision
from kuma.core.urlresolvers import reverse


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
def test_code_sample(client, settings, domain):
    """The raw source for a document can be requested."""
    url = reverse("wiki.code_sample", args=["Any/Slug", "sample1"])
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
    assert "text/plain" in response["Content-Type"]
    body = response.content.decode(response.charset)
    assert "legacy" in body.lower()
    assert "deprecated" in body.lower()


@pytest.mark.parametrize("host", ("dev.moz.org", "x.dev.moz.org", "x.y.dev.moz.org"))
def test_code_sample_host_not_allowed(settings, client, host):
    """Users are not allowed to view samples on a restricted domain."""
    url = reverse("wiki.code_sample", args=["Any/Slug", "sample1"])
    settings.DOMAIN = "dev.moz.org"
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 403


def test_code_sample_host_allowed(settings, client):
    """Users are allowed to view samples on an allowed domain."""
    host = "sampleserver"
    url = reverse("wiki.code_sample", args=["Any/Slug", "sample1"])
    settings.ATTACHMENT_HOST = host
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]


def test_code_sample_host_restricted_host(settings, client):
    """Users are allowed to view samples on the attachment domain."""
    url = reverse("wiki.code_sample", args=["Any/Slug", "sample1"])
    host = "sampleserver"
    settings.ALLOWED_HOSTS.append(host)
    settings.ATTACHMENT_HOST = host
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]


def test_raw_code_sample_file(attachment, admin_client, settings):
    filename = attachment.current_revision.filename
    settings.ATTACHMENT_HOST = "testserver"
    # Getting the URL redirects to the attachment
    file_url = reverse(
        "wiki.raw_code_sample_file",
        args=("Any/Slug", "sample1", attachment.id, filename),
    )
    response = admin_client.get(file_url)
    assert response.status_code == 302
    assert response.url == attachment.get_file_url()
    assert not response.has_header("Vary")
    assert "Cache-Control" in response
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]
