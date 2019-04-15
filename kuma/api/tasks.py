from __future__ import unicode_literals

import json

import boto3
from celery import task
from django.conf import settings

from kuma.core.utils import chunked
from kuma.wiki.models import Document

from .v1.views import document_api_data, get_content_based_redirect, get_s3_key


S3_MAX_KEYS_PER_DELETE = 1000


def get_s3_bucket():
    """ Get the S3 bucket name from the environment, otherwise None."""
    if not settings.MDN_API_S3_BUCKET_NAME:
        return None
    s3 = boto3.resource('s3')
    return s3.Bucket(settings.MDN_API_S3_BUCKET_NAME)


@task
def unpublish(doc_locale_slug_pairs, log=None, completion_message=None):
    """
    Delete one or more documents from the S3 bucket serving the document API.
    """
    if not log:
        log = unpublish.get_logger()

    s3_bucket = get_s3_bucket()
    if not s3_bucket:
        log.info('Skipping unpublish of {!r}: no S3 bucket configured'.format(
            doc_locale_slug_pairs))
        return

    keys_to_delete = (get_s3_key(locale=locale, slug=slug)
                      for locale, slug in doc_locale_slug_pairs)

    for chunk in chunked(keys_to_delete, S3_MAX_KEYS_PER_DELETE):
        response = s3_bucket.delete_objects(
            Delete={
                'Objects': [{'Key': key} for key in chunk]
            }
        )
        for info in response.get('Deleted', ()):
            log.info('Unpublished {}'.format(info['Key']))
        for info in response.get('Errors', ()):
            log.error('Unable to unpublish {}: ({}) {}'.format(
                info['Key'], info['Code'], info['Message']))

    if completion_message:
        log.info(completion_message)


@task
def publish(doc_pks, log=None, completion_message=None):
    """
    Publish one or more documents to the S3 bucket serving the document API.
    """
    if not log:
        log = publish.get_logger()

    s3_bucket = get_s3_bucket()
    if not s3_bucket:
        log.info(
            'Skipping publish of {!r}: no S3 bucket configured'.format(doc_pks))
        return

    for pk in doc_pks:
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            log.error('Document with pk={} does not exist'.format(pk))
            continue
        kwargs = dict(
            ACL='public-read',
            Key=get_s3_key(doc),
            ContentType='application/json',
            ContentLanguage=doc.locale,
        )
        redirect = get_content_based_redirect(doc)
        if redirect:
            redirect_url, is_redirect_to_document = redirect
            if is_redirect_to_document:
                kwargs.update(WebsiteRedirectLocation=redirect_url)
            else:
                data = document_api_data(redirect_url=redirect_url)
                kwargs.update(Body=json.dumps(data))
        else:
            data = document_api_data(doc, ensure_contributors=True)
            kwargs.update(Body=json.dumps(data))
        s3_object = s3_bucket.put_object(**kwargs)
        log.info('Published {!r}'.format(s3_object))

    if completion_message:
        log.info(completion_message)
