from __future__ import unicode_literals

import json
import os

import boto3
from celery import task
from django.core.mail import mail_admins

from kuma.wiki.models import Document

from .v1.views import document_api_data


@task
def publish(doc_pk, log=None, mail_admins_on_error=True):
    """
    Publish the document to the S3 bucket that serves the document API.
    """
    if not log:
        log = publish.get_logger()
    try:
        try:
            doc = Document.objects.get(pk=doc_pk)
        finally:
            doc_repr = '{}'.format(doc) if doc else 'document {}'.format(doc_pk)
        s3 = boto3.resource('s3')
        bucket_name = os.getenv('MDN_API_S3_BUCKET_NAME')
        bucket = s3.Bucket(bucket_name)
        data = document_api_data(doc, ensure_contributors=True)
        s3_object = bucket.put_object(
            ACL='public-read',
            Body=json.dumps(data),
            ContentType='application/json',
            ContentLanguage=data['locale'] or doc.locale,
            Key='api/v1/doc/{}/{}'.format(doc.locale, doc.slug),
        )
    except Exception as e:
        subject = 'Error while publishing {}'.format(doc_repr)
        log.error('{}: {}'.format(subject, e))
        if mail_admins_on_error:
            mail_admins(subject=subject, message=str(e))
    else:
        log.info('Published {!r}'.format(s3_object))


@task
def notify_publication(locale=None):
    bucket_name = os.getenv('MDN_API_S3_BUCKET_NAME')
    locale_phrase = ' within the "{}" locale'.format(locale) if locale else ''
    message = ('The command to publish all documents{} to the S3 bucket "{}" '
               'has completed.').format(locale_phrase, bucket_name)
    mail_admins(subject='Publish complete', message=message)
