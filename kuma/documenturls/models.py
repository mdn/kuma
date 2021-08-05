import requests

from django.db import models
from django.db.models.signals import pre_save
from django.dispatch import receiver
from django.utils import timezone
from redo import retry, retrying


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
        response.raise_for_status()

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

    # @classmethod
    # def download_and_store(cls, url, absolute_url, response=None, retry_options=None):
    #     response = response or download(absolute_url, retry_options=retry_options)
    #     # Because it's so big, only store certain fields that are used.
    #     full_metadata = response.json()["doc"]
    #     metadata = {}
    #     # Should we so day realize that we want to and need to store more
    #     # about the remote Yari documents, we'd simply invoke some background
    #     # processing job that forces a refresh.
    #     for key in ("title", "mdn_url", "parents"):
    #         if key in full_metadata:
    #             metadata[key] = full_metadata[key]

    #     uri = DocumentURL.normalize_uri(url)
    #     for documenturl in cls.objects.filter(
    #         uri=uri,
    #         absolute_url=absolute_url,
    #     ):
    #         documenturl.metadata = metadata
    #         documenturl.save()
    #         return documenturl, response
    #     else:
    #         return (
    #             cls.objects.create(
    #                 uri=uri, absolute_url=absolute_url, metadata=metadata
    #             ),
    #             response,
    #         )

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
        return cls.objects.update_or_create(
            uri=uri, absolute_url=absolute_url, defaults={"metadata": metadata}
        )
        # for documenturl in cls.objects.filter(
        #     uri=uri,
        #     absolute_url=absolute_url,
        # ):
        #     documenturl.metadata = metadata
        #     documenturl.save()
        #     return documenturl, response
        # else:
        #     return (
        #         cls.objects.create(
        #             uri=uri, absolute_url=absolute_url, metadata=metadata
        #         ),
        #         response,
        #     )

    # def download(self, retry_options=None):
    #     return download(self.absolute_url, retry_options=retry_options)


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

    # @classmethod
    # def check_uri(cls, document_url, cleanup_old=False, retry_options=None):
    #     _, response = DocumentURL.download_and_store(
    #         document_url.uri, document_url.absolute_url, retry_options=retry_options
    #     )
    #     headers = dict(response.headers)
    #     checked = cls.objects.create(
    #         document_url=document_url,
    #         http_error=response.status_code,
    #         headers=headers,
    #     )
    #     if cleanup_old:
    #         cls.objects.filter(document_url=document_url).exclude(
    #             id=checked.id
    #         ).delete()
    #     return checked

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
    # checked = DocumentURLCheck.check_uri(document_url, cleanup_old=cleanup_old)
    # _, response = document_url.download_and_store()
    absolute_url = document_url.absolute_url
    response = download(absolute_url, retry_options=retry_options)
    DocumentURL.store(document_url.uri, absolute_url, response)
    checked = DocumentURLCheck.store_response(
        document_url, response, cleanup_old=cleanup_old
    )
    print(f"Checked {document_url!r} and got {checked.http_error}")
    if checked.http_error == 404:
        document_url.invalid = timezone.now()
        document_url.save()
    elif checked.http_error >= 301 and checked.http_error < 400:
        # TODO: Would be nice to heed the 'location' header
        # and perhaps potentially merge this or something.
        print("A redirect!")

    # This will move the `modified` forward automatically
    document_url.save()
