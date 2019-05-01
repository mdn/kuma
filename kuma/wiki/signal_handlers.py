from django.db.models.signals import post_save
from django.dispatch import receiver

from .events import spam_attempt_email
from .jobs import (DocumentCodeSampleJob, DocumentContributorsJob,
                   DocumentTagsJob)
from .models import Document, DocumentSpamAttempt, Revision
from .signals import render_done
from .tasks import build_json_data_for_document, tidy_revision_content


@receiver(post_save, sender=Document, dispatch_uid='wiki.document.post_save')
def on_document_save(sender, instance, **kwargs):
    """
    A signal handler to be called after saving a document. Does:

    - trigger the cache invalidation of the contributor bar for the given
        document
    - trigger the renewal of the code sample job generation
    """
    DocumentContributorsJob().invalidate(instance.pk)
    DocumentTagsJob().invalidate(pk=instance.pk)

    code_sample_job = DocumentCodeSampleJob(generation_args=[instance.pk])
    code_sample_job.invalidate_generation()


@receiver(render_done, dispatch_uid='wiki.document.render_done')
def on_render_done(sender, instance, **kwargs):
    """
    A signal handler to update the given document's json field.
    """
    build_json_data_for_document.delay(instance.pk, stale=False)


@receiver(post_save, sender=Revision, dispatch_uid='wiki.revision.post_save')
def on_revision_save(sender, instance, **kwargs):
    """
    A signal handler to trigger the Celery task to update the
    tidied_content field of the given revision
    """
    tidy_revision_content.delay(instance.pk)


@receiver(post_save, sender=DocumentSpamAttempt,
          dispatch_uid='wiki.spam_attempt.post_save')
def on_document_spam_attempt_save(sender, instance, created, raw, **kwargs):
    if raw or not created:
        # Only send for new instances, not fixtures or edits
        return
    spam_attempt_email(instance).send()
