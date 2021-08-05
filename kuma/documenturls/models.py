import requests

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from redo import retrying


def download(url, retry_options=None):
    retry_options = retry_options or {
        "retry_exceptions": (
            requests.exceptions.Timeout,
            requests.exceptions.ConnectionError,
        ),
        "sleeptime": 2,
        "attempts": 5,
    }
    with retrying(requests.get, **retry_options) as retrying_get:
        response = retrying_get(url, allow_redirects=False)
        return response


class DocumentURL(models.Model):
    """There are documents we look up for things like bookmarks and notes.
    These are not legacy Wiki documents but rather remote URLs.
    """

    # E.g. /en-us/docs/web/javascript (note that it's lowercased!)
    # (the longest URI in all our of content as of mid-2021 is 121 characters)
    uri = models.CharField(max_length=250, unique=True, verbose_name="URI")
    # E.g. https://developer.allizom.org/en-us/docs/web/javascript/index.json
    absolute_url = models.URLField(verbose_name="Absolute URL")
    # If it's applicable, it's a download of the `index.json` for that URL.
    metadata = models.JSONField(null=True)
    # If the URI for some reason becomes invalid, rather than deleting it
    # or storing a boolean, note *when* it became invalid.
    invalid = models.DateTimeField(null=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Document URL"

    def __str__(self):
        return self.uri

    @classmethod
    def normalize_uri(cls, uri):
        return uri.lower().strip()

    @classmethod
    def store(cls, url, absolute_url, response):
        # Because it's so big, only store certain fields that are used.
        full_metadata = response.json()["doc"]
        metadata = {}
        # Should we so day realize that we want to and need to store more
        # about the remote Yari documents, we'd simply invoke some background
        # processing job that forces a refresh.
        for key in ("title", "mdn_url", "parents"):
            if key in full_metadata:
                metadata[key] = full_metadata[key]

        uri = DocumentURL.normalize_uri(url)
        documenturl, _ = cls.objects.update_or_create(
            uri=uri, absolute_url=absolute_url, defaults={"metadata": metadata}
        )
        return documenturl


@receiver(pre_save, sender=DocumentURL)
def assert_lowercase_uri(sender, instance, **kwargs):
    # Because it's so important that the `uri` is lowercased, this makes
    # absolutely sure it's always so.
    # Ideally, the client should check this at upsert, but if it's missed,
    # this last resort will make sure it doesn't get in in
    instance.uri = DocumentURL.normalize_uri(instance.uri)


class DocumentURLCheck(models.Model):
    document_url = models.ForeignKey(
        DocumentURL, on_delete=models.CASCADE, verbose_name="Document URL"
    )
    http_error = models.IntegerField(verbose_name="HTTP error")
    headers = models.JSONField(default=dict)
    created = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Document URL Check"

    def __str__(self):
        return f"{self.http_error} on {self.document_url.absolute_url}"

    @classmethod
    def store_response(cls, document_url, response, cleanup_old=False):
        headers = dict(response.headers)
        checked = cls.objects.create(
            document_url=document_url,
            http_error=response.status_code,
            headers=headers,
        )
        if cleanup_old:
            cls.objects.filter(document_url=document_url).exclude(
                id=checked.id
            ).delete()
        return checked


def refresh(document_url, cleanup_old=False, retry_options=None):
    absolute_url = document_url.absolute_url

    # Note that this can throw. If there's a connection error
    # or something, it will raise that error after it's done some
    # retrying.
    # This will send an error to our Sentry and it will re-try
    # again in 1h or whatever settings.REFRESH_DOCUMENTURLS_MIN_AGE_SECONDS
    # is set to.
    response = download(absolute_url, retry_options=retry_options)

    checked = DocumentURLCheck.store_response(
        document_url, response, cleanup_old=cleanup_old
    )
    print(f"Checked {document_url!r} and got {checked.http_error}")
    if checked.http_error == 200:
        DocumentURL.store(document_url.uri, absolute_url, response)
    elif checked.http_error >= 500:
        # It'll just try again later.
        pass
    elif checked.http_error == 404:
        document_url.invalid = timezone.now()
        document_url.save()
    elif checked.http_error >= 301 and checked.http_error < 400:
        # TODO: Would be nice to heed the 'location' header
        # and perhaps potentially merge this or something.
        # But because requests.get() will follow redirects it should
        # yield a response we can store at least.
        DocumentURL.store(document_url.uri, absolute_url, response)
    else:
        raise NotImplementedError(f"don't know how to deal with {checked.http_error}")
