

import json
import time

import boto3
from celery import task
from django.conf import settings
from django.utils.module_loading import import_string

from kuma.core.utils import chunked
from kuma.wiki.models import Document

from .v1.views import document_api_data, get_content_based_redirect, get_s3_key


_s3_resource = None
S3_MAX_KEYS_PER_DELETE = 1000


def get_s3_resource(config=None):
    """
    Get or create the S3 resource. This function is not thread-safe, since it
    uses the default session, rather than a separate session for each thread.
    We do not use threads however, so we don't have to handle them.
    """
    global _s3_resource
    if _s3_resource is None:
        _s3_resource = boto3.resource('s3', config=config)
    return _s3_resource


# The global cloudfront client object to be lazily defined
_cloudfront_client = None


def get_cloudfront_client(config=None):
    """
    Get or create the CloudFront client. This function is not
    thread-safe, since it uses the default session, rather than
    a separate session for each thread.
    We do not use threads however, so we don't have to handle them.
    """
    global _cloudfront_client
    if _cloudfront_client is None:
        _cloudfront_client = boto3.client('cloudfront', config=config)
    return _cloudfront_client


def get_s3_bucket(config=None):
    """
    Get the S3 bucket using the name configured in the environment, otherwise
    return None.
    """
    if not settings.MDN_API_S3_BUCKET_NAME:
        return None
    s3 = get_s3_resource(config=config)
    return s3.Bucket(settings.MDN_API_S3_BUCKET_NAME)


@task
def unpublish(doc_locale_slug_pairs, log=None, completion_message=None,
              invalidate_cdn_cache=True):
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

    if invalidate_cdn_cache:
        request_cdn_cache_invalidation.delay(doc_locale_slug_pairs)


@task
def publish(doc_pks, log=None, completion_message=None,
            invalidate_cdn_cache=True):
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

    if invalidate_cdn_cache:
        # Use this to turn the document IDs into pairs of (locale, slug).
        doc_locale_slug_pairs = []

    for pk in doc_pks:
        try:
            doc = Document.objects.get(pk=pk)
        except Document.DoesNotExist:
            log.error('Document with pk={} does not exist'.format(pk))
            continue

        if invalidate_cdn_cache:
            # Build up this list for the benefit of triggering a
            # CDN cache invalidation.
            doc_locale_slug_pairs.append((doc.locale, doc.slug))

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
            data = document_api_data(redirect_url=redirect_url)
            kwargs.update(Body=json.dumps(data))
        else:
            data = document_api_data(doc)
            kwargs.update(Body=json.dumps(data))
        s3_object = s3_bucket.put_object(**kwargs)
        log.info('Published {!r}'.format(s3_object))

    if completion_message:
        log.info(completion_message)

    if invalidate_cdn_cache and doc_locale_slug_pairs:
        request_cdn_cache_invalidation.delay(doc_locale_slug_pairs)


@task
def request_cdn_cache_invalidation(doc_locale_slug_pairs, log=None):
    """
    Trigger an attempt to purge the given documents from one or more
    of the configured CloudFront distributions.
    """
    if not log:
        log = request_cdn_cache_invalidation.get_logger()

    client = get_cloudfront_client()
    for label, conf in settings.MDN_CLOUDFRONT_DISTRIBUTIONS.items():
        if not conf['id']:
            log.info('No Distribution ID available for CloudFront {!r}'.format(
                label
            ))
            continue
        transform_function = import_string(conf['transform_function'])
        paths = (
            transform_function(locale, slug)
            for locale, slug in doc_locale_slug_pairs
        )
        # In case the transform function decided to "opt-out" on a particular
        # (locale, slug) it might return a falsy value.
        paths = [x for x in paths if x]
        if paths:
            invalidation = client.create_invalidation(
                DistributionId=conf['id'],
                InvalidationBatch={
                    'Paths': {
                        'Quantity': len(paths),
                        'Items': paths
                    },
                    # The 'CallerReference' just needs to be a unique string.
                    # By using a timestamp we get slightly more information
                    # than using a UUID or a random string. But it needs to
                    # be sufficiently "different" that's why we use 6
                    # significant figures to avoid the unlikely chance that
                    # this code gets executed concurrently within a small
                    # time window.
                    'CallerReference': '{:.6f}'.format(time.time())
                }
            )
            log.info(
                'Issued cache invalidation for {!r} in {} distribution'
                ' (received with {})'.format(
                    paths,
                    label,
                    invalidation['ResponseMetadata']['HTTPStatusCode']
                )
            )
