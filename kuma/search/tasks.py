import logging

from django.conf import settings
from django.core.mail import mail_admins

from celery.task import task

from kuma.core.decorators import skip_in_maintenance_mode


log = logging.getLogger('kuma.search.tasks')


@task
@skip_in_maintenance_mode
def prepare_index(index_pk):
    """
    Prepare a new index for indexing documents into.

    :arg index_pk: The `Index` ID to create an elasticsearch index of.

    This also updates the settings to make indexing faster, like disabling
    refreshes and replicas.

    """
    from kuma.wiki.search import WikiDocumentType
    from kuma.search.models import Index

    cls = WikiDocumentType
    es = cls.get_connection('indexing')
    index = Index.objects.get(pk=index_pk)

    # Check it if exists already. If so, delete.
    Index.objects.recreate_index(es=es, index=index)

    # Disable automatic refreshing and replicas.
    temporary_settings = {
        'index': {
            'refresh_interval': '-1',
            'number_of_replicas': '0',
        }
    }

    es.indices.put_settings(temporary_settings, index=index.prefixed_name)


@task
@skip_in_maintenance_mode
def finalize_index(index_pk):
    """
    Finalizes the elasticsearch index.

    :arg index_pk: The `Index` ID to operate on.

    This performs the following actions::
        * Optimize (which also does a refresh and a flush by default)
        * Update settings to reset number of replicas and refresh interval
        * Sends an email that the indexing is complete

    """
    from kuma.wiki.search import WikiDocumentType
    from kuma.search.models import Index

    cls = WikiDocumentType
    es = cls.get_connection('indexing')
    index = Index.objects.get(pk=index_pk)

    # Optimize.
    es.indices.optimize(index=index.prefixed_name)

    # Update the settings.
    index_settings = {
        'index': {
            'refresh_interval': settings.ES_DEFAULT_REFRESH_INTERVAL,
            'number_of_replicas': settings.ES_DEFAULT_NUM_REPLICAS,
        }
    }
    es.indices.put_settings(index=index.prefixed_name, body=index_settings)

    # Update the `Index` object and mail admins.
    index.populated = True
    index.save()

    subject = 'Index %s completely populated' % index.prefixed_name
    message = 'You may want to promote it now via the admin interface.'
    mail_admins(subject=subject, message=message)
