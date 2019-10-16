from __future__ import unicode_literals

import json
import logging

from django.conf import settings
from django.db import DatabaseError
from django.http import HttpResponse, HttpResponseBadRequest, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST, require_safe
from elasticsearch.exceptions import (ConnectionError as ES_ConnectionError,
                                      NotFoundError)
from raven.contrib.django.models import client
from requests.exceptions import (ConnectionError as Requests_ConnectionError,
                                 ReadTimeout)

from kuma.users.models import User
from kuma.wiki.kumascript import request_revision_hash
from kuma.wiki.models import Document
from kuma.wiki.search import WikiDocumentType


@never_cache
@require_safe
def liveness(request):
    """
    A successful response from this endpoint simply proves
    that Django is up and running. It doesn't mean that its
    supporting services (like MySQL, Redis, Celery) can
    be successfully used from within this service.
    """
    return HttpResponse(status=204)


@never_cache
@require_safe
def readiness(request):
    """
    A successful response from this endpoint goes a step further
    and means not only that Django is up and running, but also that
    the database can be successfully used from within this service.
    The other supporting services are not checked, but we may find
    that we want/need to add them later.
    """
    try:
        # Confirm that we can use the database by making a fast query
        # against the Document table. It's not important that the document
        # with the requested primary key exists or not, just that the query
        # completes without error.
        Document.objects.filter(pk=1).exists()
    except DatabaseError as e:
        reason_tmpl = 'service unavailable due to database issue ({!s})'
        status, reason = 503, reason_tmpl.format(e)
    else:
        status, reason = 204, None
    return HttpResponse(status=status, reason=reason)


@never_cache
@require_safe
def status(request):
    """
    Return summary information about this Kuma instance.

    Functional tests can use this to customize the test process.
    """
    data = {
        'version': 1,
        'request': {
            'url': request.build_absolute_uri(''),
            'host': request.get_host(),
            'is_secure': request.is_secure(),
            'scheme': request.scheme,
        },
        'services': {
            'database': {},
            'kumascript': {},
            'search': {},
            'test_accounts': {},
        },
        'settings': {
            'ALLOWED_HOSTS': settings.ALLOWED_HOSTS,
            'ATTACHMENT_HOST': settings.ATTACHMENT_HOST,
            'ATTACHMENT_ORIGIN': settings.ATTACHMENT_ORIGIN,
            'DEBUG': settings.DEBUG,
            'INTERACTIVE_EXAMPLES_BASE': settings.INTERACTIVE_EXAMPLES_BASE,
            'MAINTENANCE_MODE': settings.MAINTENANCE_MODE,
            'PROTOCOL': settings.PROTOCOL,
            'REVISION_HASH': settings.REVISION_HASH,
            'SITE_URL': settings.SITE_URL,
            'STATIC_URL': settings.STATIC_URL,
            'WIKI_SITE_URL': settings.WIKI_SITE_URL,
        },
    }

    # Check that database is reachable, populated
    doc_data = {
        'available': True,
        'populated': False,
        'document_count': 0
    }
    try:
        doc_count = Document.objects.count()
    except DatabaseError:
        doc_data['available'] = False
    else:
        if doc_count:
            doc_data['populated'] = True
            doc_data['document_count'] = doc_count
    data['services']['database'] = doc_data

    # Check that KumaScript is reachable
    ks_data = {
        'available': True,
        'revision': None,
    }
    try:
        ks_response = request_revision_hash()
    except (Requests_ConnectionError, ReadTimeout):
        ks_response = None
    if not ks_response or ks_response.status_code != 200:
        ks_data['available'] = False
    else:
        ks_data['revision'] = ks_response.text
    data['services']['kumascript'] = ks_data

    # Check that ElasticSearch is reachable, populated
    search_data = {
        'available': True,
        'populated': False,
        'count': 0
    }
    try:
        search_count = WikiDocumentType.search().count()
    except ES_ConnectionError:
        search_data['available'] = False
    except NotFoundError:
        pass  # available but unpopulated (and maybe uncreated)
    else:
        if search_count:
            search_data['populated'] = True
            search_data['count'] = search_count
    data['services']['search'] = search_data

    # Check if the testing accounts are available
    test_account_data = {
        'available': False
    }
    test_account_names = ['test-super', 'test-moderator', 'test-new',
                          'test-banned', 'viagra-test-123']
    try:
        users = list(User.objects.only('id', 'username', 'password')
                                 .filter(username__in=test_account_names))
    except DatabaseError:
        users = []
    if len(users) == len(test_account_names):
        for user in users:
            if not user.check_password('test-password'):
                break
        else:
            # All users have the testing password
            test_account_data['available'] = True
    data['services']['test_accounts'] = test_account_data

    return JsonResponse(data)


@csrf_exempt
@require_POST
def csp_violation_capture(request):
    """
    Capture CSP violation reports, forward to Sentry.

    HT @glogiotatidis https://github.com/mozmeao/lumbergh/pull/180
    HT @pmac, @jgmize https://github.com/mozilla/bedrock/pull/4335
    """
    if not settings.CSP_REPORT_ENABLE:
        # mitigation option for a flood of violation reports
        return HttpResponse()

    data = client.get_data_from_request(request)
    data.update({
        'level': logging.INFO,
        'logger': 'CSP',
    })
    try:
        csp_data = json.loads(request.body)
    except ValueError:
        # Cannot decode CSP violation data, ignore
        return HttpResponseBadRequest('Invalid CSP Report')

    try:
        blocked_uri = csp_data['csp-report']['blocked-uri']
    except KeyError:
        # Incomplete CSP report
        return HttpResponseBadRequest('Incomplete CSP Report')

    client.captureMessage(message='CSP Violation: {}'.format(blocked_uri),
                          data=data)

    return HttpResponse('Captured CSP violation, thanks for reporting.')
