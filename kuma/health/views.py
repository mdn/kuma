from django.conf import settings
from django.db import DatabaseError
from django.http import HttpResponse, JsonResponse
from django.views.decorators.cache import never_cache
from django.views.decorators.http import require_safe
from elasticsearch.exceptions import ConnectionError as ES_ConnectionError
from elasticsearch.exceptions import NotFoundError, TransportError
from elasticsearch_dsl import Search
from elasticsearch_dsl.connections import connections as es_connections

from kuma.users.models import User
from kuma.wiki.models import Document


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
        reason_tmpl = "service unavailable due to database issue ({!s})"
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
        "version": 1,
        "request": {
            "url": request.build_absolute_uri(""),
            "host": request.get_host(),
            "is_secure": request.is_secure(),
            "scheme": request.scheme,
        },
        "services": {
            "database": {},
            "search": {},
            "test_accounts": {},
        },
        "settings": {
            "ALLOWED_HOSTS": settings.ALLOWED_HOSTS,
            "ATTACHMENT_HOST": settings.ATTACHMENT_HOST,
            "ATTACHMENT_ORIGIN": settings.ATTACHMENT_ORIGIN,
            "ATTACHMENTS_AWS_S3_CUSTOM_URL": settings.ATTACHMENTS_AWS_S3_CUSTOM_URL,
            "DEBUG": settings.DEBUG,
            "INTERACTIVE_EXAMPLES_BASE": settings.INTERACTIVE_EXAMPLES_BASE,
            "MAINTENANCE_MODE": settings.MAINTENANCE_MODE,
            "PROTOCOL": settings.PROTOCOL,
            "REVISION_HASH": settings.REVISION_HASH,
            "SITE_URL": settings.SITE_URL,
            "STATIC_URL": settings.STATIC_URL,
        },
    }

    # Check that database is reachable, populated
    doc_data = {"available": True, "populated": False, "document_count": 0}
    try:
        doc_count = Document.objects.count()
    except DatabaseError:
        doc_data["available"] = False
    else:
        if doc_count:
            doc_data["populated"] = True
            doc_data["document_count"] = doc_count
    data["services"]["database"] = doc_data

    # Check that Elasticsearch is reachable and somewhat healthy
    search_data = {"available": None, "populated": None, "health": None, "count": None}
    try:
        es_connections.create_connection(hosts=settings.ES_URLS)
        connection = es_connections.get_connection()
        search_data["available"] = True
        health = connection.cluster.health()
        search_data["health"] = health
        count = Search(
            index=settings.SEARCH_INDEX_NAME,
        ).count()
        search_data["populated"] = count > 0
        search_data["count"] = count
    except (ES_ConnectionError, TransportError):
        search_data["available"] = False
    except NotFoundError:
        search_data["populated"] = False
    data["services"]["search"] = search_data

    # Check if the testing accounts are available
    test_account_data = {"available": False}
    test_account_names = [
        "test-super",
        "test-moderator",
        "test-new",
        "test-banned",
        "viagra-test-123",
    ]
    try:
        users = list(
            User.objects.only("id", "username", "password").filter(
                username__in=test_account_names
            )
        )
    except DatabaseError:
        users = []
    if len(users) == len(test_account_names):
        for user in users:
            if not user.check_password("test-password"):
                break
        else:
            # All users have the testing password
            test_account_data["available"] = True
    data["services"]["test_accounts"] = test_account_data

    return JsonResponse(data)
