from kuma.core.tests import assert_shared_cache_header
from kuma.core.urlresolvers import reverse

from ..utils import convert_to_http_date


def test_legacy_redirect(client, file_attachment):
    mindtouch_url = reverse(
        "attachments.mindtouch_file_redirect",
        args=(),
        kwargs={
            "file_id": file_attachment["file"]["id"],
            "filename": file_attachment["file"]["name"],
        },
    )
    response = client.get(mindtouch_url)
    assert response.status_code == 301
    assert_shared_cache_header(response)
    assert response["Location"] == file_attachment["attachment"].get_file_url()
    assert not response.has_header("Vary")


def test_raw_file_requires_attachment_host(client, settings, file_attachment):
    settings.DOMAIN = "testserver"
    settings.ATTACHMENT_HOST = "demos"
    settings.ALLOWED_HOSTS.append("demos")
    attachment = file_attachment["attachment"]
    created = attachment.current_revision.created
    url = attachment.get_file_url()

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
    if settings.ATTACHMENTS_USE_S3:
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
    else:
        assert response.status_code == 200
        assert response.streaming

    assert response["x-frame-options"] == f"ALLOW-FROM {settings.DOMAIN}"
    assert response["Last-Modified"] == convert_to_http_date(created)
    assert "public" in response["Cache-Control"]
    assert (
        f"max-age={settings.ATTACHMENTS_CACHE_CONTROL_MAX_AGE}"
        in response["Cache-Control"]
    )


def test_raw_file_if_modified_since(client, settings, file_attachment):
    settings.ATTACHMENT_HOST = "demos"
    settings.ALLOWED_HOSTS.append("demos")
    attachment = file_attachment["attachment"]
    created = attachment.current_revision.created
    url = attachment.get_file_url()

    response = client.get(
        url,
        HTTP_HOST=settings.ATTACHMENT_HOST,
        HTTP_IF_MODIFIED_SINCE=convert_to_http_date(created),
    )
    assert response.status_code == 304
    assert response["Last-Modified"] == convert_to_http_date(created)
    assert "public" in response["Cache-Control"]
    assert (
        f"max-age={settings.ATTACHMENTS_CACHE_CONTROL_MAX_AGE}"
        in response["Cache-Control"]
    )
