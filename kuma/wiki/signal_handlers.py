from django.db.models.signals import post_delete, post_save, pre_save
from django.dispatch import receiver

from .events import spam_attempt_email
from .jobs import (DocumentCodeSampleJob, DocumentContributorsJob,
                   DocumentNearestZoneJob, DocumentTagsJob,
                   DocumentZoneURLRemapsJob)
from .models import Document, DocumentSpamAttempt, DocumentZone, Revision
from .signals import render_done
from .tasks import build_json_data_for_document, tidy_revision_content


def invalidate_nearest_zone_cache(document_pk, async=False):
    """
    Reset the nearest-zone cache for this document and its descendants.
    """
    job = DocumentNearestZoneJob()
    do_invalidate = job.invalidate if async else job.refresh

    def invalidate(pk):
        do_invalidate(pk)
        # Since the descendants of this document search upwards for their
        # nearest zone, recursively invalidate their caches. Note that the
        # branches of this tree of decendants can stop at (and exclude) any
        # descendants that have their own zones.
        children = (Document.objects
                            .filter(parent_topic=pk)
                            .values_list('pk', 'zone__id'))
        for child_pk, child_zone_pk in children:
            if child_zone_pk is None:
                invalidate(child_pk)

    invalidate(document_pk)


def invalidate_zone_urls_cache(locale, async=False):
    """
    Reset the URL remap list cache for the given document, assuming it
    even has a zone.
    """
    job = DocumentZoneURLRemapsJob()
    if async:
        job.invalidate(locale)
    else:
        job.refresh(locale)


@receiver(post_save, sender=Document, dispatch_uid='wiki.document.post_save')
def on_document_save(sender, instance, **kwargs):
    """
    A signal handler to be called after saving a document. Does:

    - trigger the cache invalidation of both the zone URLs and stack
        cache for the given document
    - trigger the cache invalidation of the contributor bar for the given
        document
    - trigger the renewal of the code sample job generation
    """
    async = kwargs.get('async', True)

    if hasattr(instance, 'zone'):
        invalidate_zone_urls_cache(instance.locale, async=async)
    invalidate_nearest_zone_cache(instance.pk, async=async)

    DocumentContributorsJob().invalidate(instance.pk)
    DocumentTagsJob().invalidate(pk=instance.pk)

    code_sample_job = DocumentCodeSampleJob(generation_args=[instance.pk])
    code_sample_job.invalidate_generation()


@receiver(render_done, dispatch_uid='wiki.document.render_done')
def on_render_done(sender, instance, **kwargs):
    """
    A signal handler to update the given document's json field.
    """
    if not instance.deleted:
        build_json_data_for_document.delay(instance.pk, stale=False)


@receiver(post_save, sender=Revision, dispatch_uid='wiki.revision.post_save')
def on_revision_save(sender, instance, **kwargs):
    """
    A signal handler to trigger the Celery task to update the
    tidied_content field of the given revision
    """
    tidy_revision_content.delay(instance.pk)


@receiver(pre_save, sender=DocumentZone, dispatch_uid='wiki.zone.pre_save')
def on_zone_pre_save(sender, instance, **kwargs):
    """
    A signal handler to capture the previous state of the zone
    (from the DB) before it is lost.
    """
    # Temporarily save the previous state on the instance itself.
    dz_objs = DocumentZone.objects.values('document_id', 'document__locale')
    try:
        instance.previous = dz_objs.get(pk=instance.pk)
    except DocumentZone.DoesNotExist:
        # This will happen for newly-created zones.
        instance.previous = None


@receiver(post_save, sender=DocumentZone, dispatch_uid='wiki.zone.post_save')
def on_zone_post_save(sender, instance, **kwargs):
    """
    A signal handler to trigger cache invalidation for this zone.
    """
    if instance.previous:
        if instance.document.pk != instance.previous['document_id']:
            invalidate_nearest_zone_cache(instance.previous['document_id'])
            invalidate_zone_urls_cache(instance.previous['document__locale'])
        # Now that we've used the previous state of the zone, clear it.
        instance.previous = None

    invalidate_nearest_zone_cache(instance.document.pk)
    invalidate_zone_urls_cache(instance.document.locale)


@receiver(post_delete, sender=DocumentZone,
          dispatch_uid='wiki.zone.post_delete')
def on_zone_delete(sender, instance, **kwargs):
    """
    A signal handler to trigger cache invalidation for this zone.
    """
    invalidate_nearest_zone_cache(instance.document.pk)
    invalidate_zone_urls_cache(instance.document.locale)


@receiver(post_save, sender=DocumentSpamAttempt,
          dispatch_uid='wiki.spam_attempt.post_save')
def on_document_spam_attempt_save(sender, instance, created, raw, **kwargs):
    if raw or not created:
        # Only send for new instances, not fixtures or edits
        return
    spam_attempt_email(instance).send()
