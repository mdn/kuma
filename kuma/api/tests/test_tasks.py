from __future__ import unicode_literals

import json

import mock
import pytest

from kuma.api.tasks import publish, unpublish
from kuma.api.v1.views import document_api_data, get_s3_key
from kuma.wiki.templatetags.jinja_helpers import absolutify


def get_mocked_s3_bucket():

    def get_s3_response(**kwargs):
        deleted = kwargs['Delete']['Objects']
        if len(deleted) > 1:
            if len(deleted) == 2:
                # Let's make them all errors.
                errors = [deleted[0].copy(), deleted[1].copy()]
                for error in errors:
                    error.update(Code='InternalError', Message='Some error')
                # S3 excludes the "Deleted" key from its response
                # if there are none.
                return {
                    'Errors': errors
                }
            # Otherwise, let's make the first one an error.
            error = deleted[0].copy()
            error.update(Code='InternalError', Message='Some error')
            return {
                'Deleted': deleted[1:],
                'Errors': [error]
            }
        # S3 excludes the "Errors" key from its response if there are none.
        return {
            'Deleted': deleted
        }

    s3_object_mock = mock.Mock()
    s3_object_mock.__repr__ = mock.Mock(
        side_effect=['S3 Object #1', 'S3 Object #2', 'S3 Object #3']
    )
    s3_bucket_mock = mock.Mock()
    s3_bucket_mock.put_object = mock.Mock(return_value=s3_object_mock)
    s3_bucket_mock.delete_objects = mock.Mock(side_effect=get_s3_response)
    return s3_bucket_mock


def test_publish_no_s3_bucket_configured(root_doc):
    """Test the publish task when no S3 bucket is configured."""
    log_mock = mock.Mock()
    doc_pks = [root_doc.pk]
    publish(doc_pks, log=log_mock)
    log_mock.info.assert_called_once_with(
        'Skipping publish of {!r}: no S3 bucket configured'.format(doc_pks))


@mock.patch('kuma.api.tasks.get_s3_bucket')
def test_publish_standard(get_s3_bucket_mock, root_doc):
    """Test the publish task for a standard (non-redirect) document."""
    log_mock = mock.Mock()
    get_s3_bucket_mock.return_value = s3_bucket_mock = get_mocked_s3_bucket()
    publish.get_logger = mock.Mock(return_value=log_mock)
    publish([root_doc.pk])
    s3_bucket_mock.put_object.assert_called_once_with(
        ACL='public-read',
        Key=get_s3_key(root_doc),
        Body=json.dumps(document_api_data(root_doc, ensure_contributors=True)),
        ContentType='application/json',
        ContentLanguage=root_doc.locale
    )
    log_mock.info.assert_called_once_with('Published S3 Object #1')


@mock.patch('kuma.api.tasks.get_s3_bucket')
def test_publish_redirect(get_s3_bucket_mock, root_doc, redirect_doc):
    """
    Test the publish task for a document that redirects to another document
    within the S3 bucket.
    """
    log_mock = mock.Mock()
    get_s3_bucket_mock.return_value = s3_bucket_mock = get_mocked_s3_bucket()
    publish([redirect_doc.pk], log=log_mock)
    s3_bucket_mock.put_object.assert_called_once_with(
        ACL='public-read',
        Key=get_s3_key(redirect_doc),
        WebsiteRedirectLocation=get_s3_key(root_doc, for_redirect=True),
        ContentType='application/json',
        ContentLanguage=redirect_doc.locale
    )
    log_mock.info.assert_called_once_with('Published S3 Object #1')


@mock.patch('kuma.api.tasks.get_s3_bucket')
def test_publish_redirect_to_home(get_s3_bucket_mock, redirect_to_home):
    """
    Test the publish task for a document that redirects to a URL outside the
    S3 bucket, in this case the home page.
    """
    log_mock = mock.Mock()
    get_s3_bucket_mock.return_value = s3_bucket_mock = get_mocked_s3_bucket()
    publish([redirect_to_home.pk], log=log_mock)
    s3_bucket_mock.put_object.assert_called_once_with(
        ACL='public-read',
        Key=get_s3_key(redirect_to_home),
        Body=json.dumps(document_api_data(redirect_url='/en-US/')),
        ContentType='application/json',
        ContentLanguage=redirect_to_home.locale
    )
    log_mock.info.assert_called_once_with('Published S3 Object #1')


@mock.patch('kuma.api.tasks.get_s3_bucket')
def test_publish_redirect_to_other(get_s3_bucket_mock, redirect_to_macros):
    """
    Test the publish task for a document that redirects to a URL outside the
    S3 bucket, in this case someting other than the home page.
    """
    log_mock = mock.Mock()
    get_s3_bucket_mock.return_value = s3_bucket_mock = get_mocked_s3_bucket()
    publish([redirect_to_macros.pk], log=log_mock)
    s3_bucket_mock.put_object.assert_called_once_with(
        ACL='public-read',
        Key=get_s3_key(redirect_to_macros),
        Body=json.dumps(document_api_data(
            redirect_url=absolutify('/en-US/dashboards/macros',
                                    for_wiki_site=True))),
        ContentType='application/json',
        ContentLanguage=redirect_to_macros.locale
    )
    log_mock.info.assert_called_once_with('Published S3 Object #1')


@mock.patch('kuma.api.tasks.get_s3_bucket')
def test_publish_multiple(get_s3_bucket_mock, root_doc, redirect_doc,
                          redirect_to_home, trans_doc):
    """
    Test the publish task for multiple documents of various kinds, including
    standard documents and redirects.
    """
    trans_doc.delete()
    log_mock = mock.Mock()
    get_s3_bucket_mock.return_value = s3_bucket_mock = get_mocked_s3_bucket()
    publish([trans_doc.pk, root_doc.pk, redirect_doc.pk, redirect_to_home.pk],
            log=log_mock, completion_message='Done!')
    s3_bucket_mock.put_object.assert_has_calls([
        mock.call(
            ACL='public-read',
            Key=get_s3_key(root_doc),
            Body=json.dumps(
                document_api_data(root_doc, ensure_contributors=True)),
            ContentType='application/json',
            ContentLanguage=root_doc.locale
        ),
        mock.call(
            ACL='public-read',
            Key=get_s3_key(redirect_doc),
            WebsiteRedirectLocation=get_s3_key(root_doc, for_redirect=True),
            ContentType='application/json',
            ContentLanguage=redirect_doc.locale
        ),
        mock.call(
            ACL='public-read',
            Key=get_s3_key(redirect_to_home),
            Body=json.dumps(document_api_data(redirect_url='/en-US/')),
            ContentType='application/json',
            ContentLanguage=redirect_to_home.locale
        ),
    ])
    log_mock.error.assert_called_once_with(
        'Document with pk={} does not exist'.format(trans_doc.pk))
    log_mock.info.assert_has_calls([
        mock.call('Published S3 Object #1'),
        mock.call('Published S3 Object #2'),
        mock.call('Published S3 Object #3'),
        mock.call('Done!'),
    ])


def test_unpublish_no_s3_bucket_configured(root_doc):
    """Test the unpublish task when no S3 bucket is configured."""
    log_mock = mock.Mock()
    doc_locale_slug_pairs = [(root_doc.locale, root_doc.slug)]
    unpublish(doc_locale_slug_pairs, log=log_mock)
    log_mock.info.assert_called_once_with(
        'Skipping unpublish of {!r}: no S3 bucket configured'.format(
            doc_locale_slug_pairs))


@pytest.mark.parametrize('case', ('un-deleted', 'deleted', 'purged'))
@mock.patch('kuma.api.tasks.get_s3_bucket')
def test_unpublish(get_s3_bucket_mock, root_doc, case):
    """Test the unpublish task for a single document."""
    if case in ('deleted', 'purged'):
        if case == 'purged':
            root_doc.delete()
    log_mock = mock.Mock()
    s3_bucket_mock = get_mocked_s3_bucket()
    get_s3_bucket_mock.return_value = s3_bucket_mock
    unpublish.get_logger = mock.Mock(return_value=log_mock)
    unpublish([(root_doc.locale, root_doc.slug)])
    s3_key = get_s3_key(root_doc)
    s3_bucket_mock.delete_objects.assert_called_once_with(
        Delete={
            'Objects': [
                {
                    'Key': s3_key
                }
            ]
        }
    )
    log_mock.info.assert_called_once_with('Unpublished {}'.format(s3_key))


@mock.patch('kuma.api.tasks.get_s3_bucket')
def test_unpublish_multiple(get_s3_bucket_mock, root_doc, redirect_doc,
                            redirect_to_home):
    """
    Test the unpublish task for multiple documents of various kinds, including
    standard documents and redirects.
    """
    log_mock = mock.Mock()
    docs = (root_doc, redirect_doc, redirect_to_home)
    doc_locale_slug_pairs = [(doc.locale, doc.slug) for doc in docs]
    get_s3_bucket_mock.return_value = s3_bucket_mock = get_mocked_s3_bucket()
    unpublish(doc_locale_slug_pairs, log=log_mock, completion_message='Done!')
    s3_keys = tuple(get_s3_key(doc) for doc in docs)
    s3_bucket_mock.delete_objects.assert_called_once_with(
        Delete={
            'Objects': [
                {
                    'Key': key
                }
                for key in s3_keys
            ]
        }
    )
    log_mock.error.assert_called_once_with(
        'Unable to unpublish {}: (InternalError) Some error'.format(s3_keys[0])
    )
    log_mock.info.assert_has_calls(
        [mock.call('Unpublished {}'.format(key)) for key in s3_keys[1:]] +
        [mock.call('Done!')]
    )


@mock.patch('kuma.api.tasks.get_s3_bucket')
@mock.patch('kuma.api.tasks.S3_MAX_KEYS_PER_DELETE', 2)
def test_unpublish_multiple_chunked(get_s3_bucket_mock, root_doc, redirect_doc,
                                    redirect_to_home):
    """
    Test the unpublish task for multiple documents where the deletes are
    broken-up into chunks.
    """
    log_mock = mock.Mock()
    docs = (root_doc, redirect_doc, redirect_to_home)
    doc_locale_slug_pairs = [(doc.locale, doc.slug) for doc in docs]
    get_s3_bucket_mock.return_value = s3_bucket_mock = get_mocked_s3_bucket()
    unpublish(doc_locale_slug_pairs, log=log_mock, completion_message='Done!')
    s3_keys = tuple(get_s3_key(doc) for doc in docs)
    s3_bucket_mock.delete_objects.assert_has_calls([
        mock.call(
            Delete={
                'Objects': [
                    {
                        'Key': key
                    }
                    for key in s3_keys[:2]
                ]
            }
        ),
        mock.call(
            Delete={
                'Objects': [
                    {
                        'Key': key
                    }
                    for key in s3_keys[2:]
                ]
            }
        )
    ])
    log_mock.error.assert_has_calls([
        mock.call(
            'Unable to unpublish {}: (InternalError) Some error'.format(key))
        for key in s3_keys[:2]
    ])
    log_mock.info.assert_has_calls([
        mock.call('Unpublished {}'.format(s3_keys[-1])),
        mock.call('Done!')
    ])
