import pytest

from kuma.core.urlresolvers import reverse


@pytest.mark.parametrize("domain", ("HOST", "ORIGIN"))
def test_code_sample(client, settings, domain):
    """The raw source for a document can be requested."""
    url = reverse("wiki.code_sample", args=["AnySlug", "sample1"])
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
    url = reverse("wiki.code_sample", args=["AnySlug", "sample1"])
    settings.DOMAIN = "dev.moz.org"
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 403


def test_code_sample_host_allowed(settings, client):
    """Users are allowed to view samples on an allowed domain."""
    host = "sampleserver"
    url = reverse("wiki.code_sample", args=["AnySlug", "sample1"])
    settings.ATTACHMENT_HOST = host
    settings.ALLOWED_HOSTS.append(host)
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]


def test_code_sample_host_restricted_host(settings, client):
    """Users are allowed to view samples on the attachment domain."""
    url = reverse("wiki.code_sample", args=["AnySlug", "sample1"])
    host = "sampleserver"
    settings.ALLOWED_HOSTS.append(host)
    settings.ATTACHMENT_HOST = host
    settings.ENABLE_RESTRICTIONS_BY_HOST = True
    response = client.get(url, HTTP_HOST=host)
    assert response.status_code == 200
    assert "public" in response["Cache-Control"]
    assert "max-age=31536000" in response["Cache-Control"]
