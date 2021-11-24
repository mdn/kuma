from kuma.core.urlresolvers import reverse

from ..utils import full_attachment_url, full_mindtouch_attachment_url


def test_mindtouch_redirect(client, settings, sample_mindtouch_attachment_redirect):

    settings.DOMAIN = "testserver"
    settings.ATTACHMENT_HOST = "demos"
    settings.ALLOWED_HOSTS.append("demos")

    filename = sample_mindtouch_attachment_redirect["url"].split("/")[-1]
    id = sample_mindtouch_attachment_redirect["id"]
    mindtouch_url = reverse(
        "attachments.mindtouch_file_redirect",
        args=(),
        kwargs={
            "file_id": id,
            "filename": filename,
        },
    )
    response = client.get(mindtouch_url, HTTP_HOST=settings.ATTACHMENT_HOST)
    assert response.status_code == 302
    # Figure out the external scheme + host for our attachments bucket
    endpoint_url = settings.ATTACHMENTS_AWS_S3_ENDPOINT_URL
    custom_proto = "https" if settings.ATTACHMENTS_AWS_S3_SECURE_URLS else "http"
    custom_url = f"{custom_proto}://{settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN}"
    bucket_url = (
        custom_url if settings.ATTACHMENTS_AWS_S3_CUSTOM_DOMAIN else endpoint_url
    )

    # Verify we're redirecting to the intended bucket or custom frontend
    assert response["location"].startswith(bucket_url)

    assert response["x-frame-options"] == f"ALLOW-FROM {settings.DOMAIN}"
    assert response["Last-Modified"]


def test_mindtouch_redirect_requires_attachment_host(
    client, settings, sample_mindtouch_attachment_redirect
):

    settings.DOMAIN = "testserver"
    settings.ATTACHMENT_HOST = "demos"
    settings.ALLOWED_HOSTS.append("demos")

    filename = sample_mindtouch_attachment_redirect["url"].split("/")[-1]
    id = sample_mindtouch_attachment_redirect["id"]
    mindtouch_url = reverse(
        "attachments.mindtouch_file_redirect",
        args=(),
        kwargs={
            "file_id": id,
            "filename": filename,
        },
    )
    # Note! Not using the correct `HTTP_HOST=settings.ATTACHMENT_HOST`
    response = client.get(mindtouch_url)
    assert response.status_code == 301
    url = full_mindtouch_attachment_url(id, filename)
    assert response["Location"] == url


def test_mindtouch_not_found(client, settings):

    settings.DOMAIN = "testserver"
    settings.ATTACHMENT_HOST = "demos"
    settings.ALLOWED_HOSTS.append("demos")

    mindtouch_url = reverse(
        "attachments.mindtouch_file_redirect",
        args=(),
        kwargs={
            "file_id": 12345678,
            "filename": "anything.png",
        },
    )
    response = client.get(mindtouch_url)
    assert response.status_code == 404


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
    assert response["Location"] == url

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


def test_raw_file_not_found(client, settings):
    settings.DOMAIN = "testserver"
    settings.ATTACHMENT_HOST = "demos"
    settings.ALLOWED_HOSTS.append("demos")

    # Any ID we definitely know is not in the 'redirects.json' file
    url = full_attachment_url(12345678, "foo.png")
    response = client.get(url, HTTP_HOST=settings.ATTACHMENT_HOST)
    assert response.status_code == 404
