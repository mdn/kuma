from kuma.core.tests import assert_shared_cache_header
from kuma.core.urlresolvers import reverse

from ..utils import full_attachment_url


def test_legacy_redirect(client, settings, sample_attachment_redirect):
    filename = sample_attachment_redirect["url"].split("/")[-1]
    id = sample_attachment_redirect["id"]
    mindtouch_url = reverse(
        "attachments.mindtouch_file_redirect",
        args=(),
        kwargs={
            "file_id": id,
            "filename": filename,
        },
    )
    response = client.get(mindtouch_url)
    assert response.status_code == 301
    assert_shared_cache_header(response)
    assert (
        response["Location"]
        == f"http://{settings.ATTACHMENT_HOST}/files/{id}/{filename}"
    )
    assert not response.has_header("Vary")


def test_raw_file_requires_attachment_host(
    client, settings, sample_attachment_redirect
):
    settings.DOMAIN = "testserver"
    settings.ATTACHMENT_HOST = "demos"
    settings.ALLOWED_HOSTS.append("demos")

    filename = sample_attachment_redirect["url"].split("/")[-1]
    url = full_attachment_url(sample_attachment_redirect["id"], filename)
    # Force the HOST header to look like something other than "demos".
    response = client.get(url, HTTP_HOST="testserver")
    assert response.status_code == 301
    assert "public" in response["Cache-Control"]
    assert (
        f"max-age={settings.ATTACHMENTS_CACHE_CONTROL_MAX_AGE}"
        in response["Cache-Control"]
    )
    assert response["Location"] == url
    assert "Vary" not in response

    response = client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
    # Figure out the external scheme + host for our attachments bucket
    endpoint_url = settings.ATTACHMENTS_AWS_S3_ENDPOINT_URL
    custom_proto = "https" if settings.ATTACHMENTS_AWS_S3_SECURE_URLS else "http"
    custom_url = f"{custom_proto}://{settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN}"
    bucket_url = (
        custom_url if settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN else endpoint_url
    )

    # Verify we're redirecting to the intended bucket or custom frontend
    assert response.status_code == 302
    assert response["location"].startswith(bucket_url)

    assert response["x-frame-options"] == f"ALLOW-FROM {settings.DOMAIN}"
    assert response["Last-Modified"]
    assert "public" in response["Cache-Control"]
    assert (
        f"max-age={settings.ATTACHMENTS_CACHE_CONTROL_MAX_AGE}"
        in response["Cache-Control"]
    )
