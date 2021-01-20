import json
import logging
import textwrap
from datetime import datetime, timedelta

from celery import task
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.mail import mail_admins
from django.db import transaction

from kuma.core.decorators import skip_in_maintenance_mode
from kuma.core.utils import send_mail_retrying
from kuma.users.models import User

from .events import first_edit_email
from .exceptions import PageMoveError
from .models import (
    Document,
    DocumentDeletionLog,
    DocumentRenderingInProgress,
    DocumentSpamAttempt,
    Revision,
    RevisionIP,
)


log = logging.getLogger("kuma.wiki.tasks")


@task(rate_limit="60/m")
@skip_in_maintenance_mode
def render_document(
    pk, cache_control, base_url, force=False, invalidate_cdn_cache=True
):
    """Simple task wrapper for the render() method of the Document model"""
    document = Document.objects.get(pk=pk)
    if force:
        document.render_started_at = None

    try:
        document.render(
            cache_control, base_url, invalidate_cdn_cache=invalidate_cdn_cache
        )
    except DocumentRenderingInProgress:
        pass
    except Exception as e:
        subject = "Exception while rendering document %s" % document.pk
        mail_admins(subject=subject, message=str(e))
    return document.rendered_errors


@task
@skip_in_maintenance_mode
def email_document_progress(command_name, percent_complete, total):
    """
    Task to send email for progress notification.
    """
    subject = "The command `{}` is {}% complete".format(command_name, percent_complete)
    message = "{} out of a total of {} documents.".format(subject, total)
    mail_admins(subject=subject, message=message)


@task
@skip_in_maintenance_mode
def render_document_chunk(
    pks,
    cache_control="no-cache",
    base_url=None,
    force=False,
    invalidate_cdn_cache=False,
):
    """
    Simple task to render a chunk of documents instead of one per each
    """
    logger = render_document_chunk.get_logger()
    logger.info(
        "Starting to render document chunk: %s" % ",".join([str(pk) for pk in pks])
    )
    base_url = base_url or settings.SITE_URL
    for pk in pks:
        # calling the task without delay here since we want to localize
        # the processing of the chunk in one process
        result = render_document(
            pk,
            cache_control,
            base_url,
            force=force,
            invalidate_cdn_cache=invalidate_cdn_cache,
        )
        if result:
            logger.error(
                "Error while rendering document %s with error: %s" % (pk, result)
            )
    logger.info("Finished rendering of document chunk")


@task
@skip_in_maintenance_mode
def clean_document_chunk(doc_pks, user_pk):
    """
    Simple task to clean a chunk of documents.
    """
    logger = clean_document_chunk.get_logger()
    logger.info(
        "Starting to clean document chunk: {}".format(
            ",".join(str(pk) for pk in doc_pks)
        )
    )
    user = User.objects.get(pk=user_pk)
    num_cleaned = 0
    for pk in doc_pks:
        try:
            doc = Document.objects.get(pk=pk)
            logger.info("   Cleaning {!r}".format(doc))
            rev = doc.clean_current_revision(user)
        except Exception as e:
            logger.info("   ...mailing error to admins")
            subject = "Error while cleaning document {}".format(pk)
            mail_admins(subject=subject, message=str(e))
        else:
            if rev is None:
                logger.info("   ...skipped (it's already clean)")
            else:
                num_cleaned += 1
                logger.info("   ...created {!r}".format(rev))
    logger.info(
        "Finished cleaning document chunk ({} of {} "
        "required cleaning)".format(num_cleaned, len(doc_pks))
    )


@task
@skip_in_maintenance_mode
def build_json_data_for_document(pk, stale):
    """Force-refresh cached JSON data after rendering."""
    document = Document.objects.get(pk=pk)
    document.get_json_data(stale=stale)

    # If we're a translation, rebuild our source doc's JSON so its
    # translation list includes our last edit date.
    if document.parent is not None:
        parent_json = json.dumps(document.parent.build_json_data())
        Document.objects.filter(pk=document.parent.pk).update(json=parent_json)


@task
@skip_in_maintenance_mode
def move_page(locale, slug, new_slug, user_id):
    transaction.set_autocommit(False)
    User = get_user_model()
    try:
        user = User.objects.get(id=user_id)
    except User.DoesNotExist:
        transaction.rollback()
        logging.error("Page move failed: no user with id %s" % user_id)
        return

    try:
        doc = Document.objects.get(locale=locale, slug=slug)
    except Document.DoesNotExist:
        transaction.rollback()
        message = """
            Page move failed.

            Move was requested for document with slug %(slug)s in locale
            %(locale)s, but no such document exists.
        """ % {
            "slug": slug,
            "locale": locale,
        }
        logging.error(message)
        send_mail_retrying(
            "Page move failed",
            textwrap.dedent(message),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        transaction.set_autocommit(True)
        return

    try:
        doc._move_tree(new_slug, user=user)
    except PageMoveError as e:
        transaction.rollback()
        message = """
            Page move failed.

            Move was requested for document with slug %(slug)s in locale
            %(locale)s, but could not be completed.

            Diagnostic info:

            %(message)s
        """ % {
            "slug": slug,
            "locale": locale,
            "message": e.message,
        }
        logging.error(message)
        send_mail_retrying(
            "Page move failed",
            textwrap.dedent(message),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        transaction.set_autocommit(True)
        return
    except Exception as e:
        transaction.rollback()
        message = """
            Page move failed.

            Move was requested for document with slug %(slug)s in locale %(locale)s,
            but could not be completed.

            %(info)s
        """ % {
            "slug": slug,
            "locale": locale,
            "info": e,
        }
        logging.error(message)
        send_mail_retrying(
            "Page move failed",
            textwrap.dedent(message),
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
        )
        transaction.set_autocommit(True)
        return

    transaction.commit()
    transaction.set_autocommit(True)

    # Now that we know the move succeeded, re-render the whole tree.
    for moved_doc in [doc] + doc.get_descendants():
        moved_doc.schedule_rendering("max-age=0")

    subject = "Page move completed: " + slug + " (" + locale + ")"

    full_url = settings.SITE_URL + "/" + locale + "/docs/" + new_slug

    # Get the parent document, if parent doc is None, it means its the parent document
    parent_doc = doc.parent or doc

    other_locale_urls = [
        settings.SITE_URL + translation.get_absolute_url()
        for translation in parent_doc.translations.exclude(locale=doc.locale).order_by(
            "locale"
        )
    ]

    # If the document is a translation we should include the parent document url to the list
    if doc.parent:
        other_locale_urls = [
            settings.SITE_URL + doc.parent.get_absolute_url()
        ] + other_locale_urls

    message = textwrap.dedent(
        """
        Page move completed.

        The move requested for the document with slug %(slug)s in locale
        %(locale)s, and all its children, has been completed.

        The following localized articles may need to be moved also:
        %(locale_urls)s

        You can now view this document at its new location: %(full_url)s.
    """
    ) % {
        "slug": slug,
        "locale": locale,
        "full_url": full_url,
        "locale_urls": "\n".join(other_locale_urls),
    }

    send_mail_retrying(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])


@task
@skip_in_maintenance_mode
def delete_old_revision_ips(days=30):
    RevisionIP.objects.delete_old(days=days)


@task
@skip_in_maintenance_mode
def send_first_edit_email(revision_pk):
    """ Make an 'edited' notification email for first-time editors """
    revision = Revision.objects.get(pk=revision_pk)
    first_edit_email(revision).send()


@task
@skip_in_maintenance_mode
def delete_old_documentspamattempt_data(days=30):
    """Delete old DocumentSpamAttempt.data, which contains PII.

    Also set review to REVIEW_UNAVAILABLE.
    """
    older = datetime.now() - timedelta(days=30)
    dsas = DocumentSpamAttempt.objects.filter(created__lt=older).exclude(
        data__isnull=True
    )
    dsas_reviewed = dsas.exclude(review=DocumentSpamAttempt.NEEDS_REVIEW)
    dsas_unreviewed = dsas.filter(review=DocumentSpamAttempt.NEEDS_REVIEW)
    dsas_reviewed.update(data=None)
    dsas_unreviewed.update(data=None, review=DocumentSpamAttempt.REVIEW_UNAVAILABLE)


@task
@skip_in_maintenance_mode
def delete_logs_for_purged_documents():
    """Delete DocumentDeletionLogs for purged documents."""
    for ddl in DocumentDeletionLog.objects.all():
        doc = Document.admin_objects.filter(locale=ddl.locale, slug=ddl.slug)
        if not doc.exists():
            ddl.delete()
