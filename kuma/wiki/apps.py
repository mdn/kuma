from constance import config

from django.apps import AppConfig
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.core.mail import send_mail
from django.db.models import signals
from django.template.loader import render_to_string
from django.utils.translation import ugettext_lazy as _

from elasticsearch_dsl.connections import connections as es_connections

from .jobs import (DocumentContributorsJob, DocumentZoneStackJob,
                   DocumentZoneURLRemapsJob, DocumentCodeSampleJob)
from .signals import render_done


def invalidate_zone_stack_cache(document, async=False):
    """
    Reset the cache for the zone stack for all of the documents
    in the document tree branch.
    """
    pks = [document.pk] + [parent.pk for parent in
                           document.get_topic_parents()]
    job = DocumentZoneStackJob()
    if async:
        invalidator = job.invalidate
    else:
        invalidator = job.refresh
    for pk in pks:
        invalidator(pk)


def invalidate_zone_urls_cache(document, async=False):
    """
    Reset the URL remap list cache for the given document, assuming it
    even has a zone.
    """
    job = DocumentZoneURLRemapsJob()
    if async:
        invalidator = job.invalidate
    else:
        invalidator = job.refresh
    try:
        if document.zone:
            # reset the cached list of zones of the document's locale
            invalidator(document.locale)
    except ObjectDoesNotExist:
        pass


class WikiConfig(AppConfig):
    """
    The Django App Config class to store information about the wiki app
    and do startup time things.
    """
    name = 'kuma.wiki'
    verbose_name = _("Wiki")

    def ready(self):
        super(WikiConfig, self).ready()

        # Configure Elasticsearch connections for connection pooling.
        es_connections.configure(
            default={
                'hosts': settings.ES_URLS,
            },
            indexing={
                'hosts': settings.ES_URLS,
                'timeout': settings.ES_INDEXING_TIMEOUT,
            },
        )

        # connect some signal handlers for the wiki models
        Document = self.get_model('Document')
        signals.post_save.connect(self.on_document_save,
                                  sender=Document,
                                  dispatch_uid='wiki.document.post_save')
        render_done.connect(self.on_render_done,
                            dispatch_uid='wiki.document.render_done')

        Revision = self.get_model('Revision')
        signals.post_save.connect(self.on_revision_save,
                                  sender=Revision,
                                  dispatch_uid='wiki.revision.post_save')

        DocumentZone = self.get_model('DocumentZone')
        signals.post_save.connect(self.on_zone_save,
                                  sender=DocumentZone,
                                  dispatch_uid='wiki.zone.post_save')

        DocumentSpamAttempt = self.get_model('DocumentSpamAttempt')
        signals.post_save.connect(self.on_document_spam_attempt_save,
                                  sender=DocumentSpamAttempt,
                                  dispatch_uid='wiki.spam_attempt.post_save')

    def on_document_save(self, sender, instance, **kwargs):
        """
        A signal handler to be called after saving a document. Does:

        - trigger the cache invalidation of both the zone URLs and stack
          cache for the given document
        - trigger the cache invalidation of the contributor bar for the given
          document
        - trigger the renewal of the code sample job generation
        """
        async = kwargs.get('async', True)

        invalidate_zone_urls_cache(instance, async=async)
        invalidate_zone_stack_cache(instance, async=async)

        DocumentContributorsJob().invalidate(instance.pk)

        code_sample_job = DocumentCodeSampleJob(generation_args=[instance.pk])
        code_sample_job.invalidate_generation()

    def on_zone_save(self, sender, instance, **kwargs):
        """
        A signal handler to trigger the cache invalidation of both the zone
        URLs and stack cache for a given zone's document.
        """
        self.on_document_save(sender=instance.document.__class__,
                              instance=instance.document,
                              async=False)

    def on_render_done(self, sender, instance, **kwargs):
        """
        A signal handler to update the given document's json field.
        """
        from .tasks import build_json_data_for_document
        if not instance.deleted:
            build_json_data_for_document.delay(instance.pk, stale=False)

    def on_revision_save(self, sender, instance, **kwargs):
        """
        A signal handler to trigger the Celery task to update the
        tidied_content field of the given revision
        """
        from .tasks import tidy_revision_content
        tidy_revision_content.delay(instance.pk)

    def on_document_spam_attempt_save(
            self, sender, instance, created, raw, **kwargs):
        if raw or not created:
            # Only send for new instances, not fixtures or edits
            return
        subject = u'[MDN] Wiki spam attempt recorded'
        if instance.document:
            subject = u'%s for document %s' % (subject, instance.document)
        elif instance.title:
            subject = u'%s with title %s' % (subject, instance.title)
        body = render_to_string('wiki/email/spam.ltxt',
                                {'spam_attempt': instance})
        send_mail(subject, body, settings.DEFAULT_FROM_EMAIL,
                  [config.EMAIL_LIST_SPAM_WATCH])
