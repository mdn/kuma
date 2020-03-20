from collections import defaultdict

from django.core.management.base import BaseCommand
from django.db import models
from django.utils.text import get_text_list

from kuma.attachments.models import Attachment

from ...constants import DEKI_FILE_URL, KUMA_FILE_URL
from ...models import Document, DocumentAttachment


class Command(BaseCommand):
    help = "Populate m2m relations for documents and their attachments"

    def add_arguments(self, parser):
        parser.add_argument(
            "-n",
            "--dry-run",
            action="store_true",
            dest="dry_run",
            default=False,
            help="Do everything except actually populating " "the attachments.",
        )

    def attachments_documents_map(self):
        """
        Builds and returns a mapping between attachment IDs and a list of IDs
        of the documents whose content contained the attachment URL.
        """
        mapping = defaultdict(list)
        documents = Document.admin_objects.exclude(is_redirect=True).only("pk", "html")

        self.stdout.write(
            "Attaching files to %s documents...\n\n" % documents.approx_count()
        )

        for document in documents.iterator():
            mt_files = DEKI_FILE_URL.findall(document.html)
            kuma_files = KUMA_FILE_URL.findall(document.html)
            params = None

            if mt_files:
                params = models.Q(mindtouch_attachment_id__in=mt_files)
                if kuma_files:
                    params = params | models.Q(id__in=kuma_files)
            if kuma_files and not params:
                params = models.Q(id__in=kuma_files)

            if params:
                attachment_pks = (
                    Attachment.objects.filter(params)
                    .distinct()
                    .values_list("pk", flat=True)
                )
                for attachment_pk in attachment_pks:
                    mapping[attachment_pk].append(document.pk)

        return mapping

    def create_attachment(self, document, attachment, revision, is_original):
        """
        Creates a M2M relationship between the given document and attachment
        using some metadata of the given revision (the latest most likely) and
        either as an original or as a non-originally uploaded file.
        """
        if not self.dry_run:
            relation, created = DocumentAttachment.objects.update_or_create(
                file_id=attachment.pk,
                document_id=document.pk,
                defaults={
                    "attached_by": revision.creator,
                    "name": revision.filename,
                    "is_original": is_original,
                    # all relations are linked since they were found in
                    # the document's content
                    "is_linked": True,
                },
            )
        self.attached.append(attachment.pk)

    def handle(self, *args, **options):
        self.dry_run = options["dry_run"]
        self.attached = []

        # first get the attachment to document list mapping
        mapping = self.attachments_documents_map()
        for attachment_pk, document_pks in mapping.items():
            # get the attachment
            attachment = Attachment.objects.only("pk", "current_revision").get(
                pk=attachment_pk
            )
            if not attachment.current_revision:
                # bail if there isn't a current attachment revision
                # probably because faulty data
                self.stderr.write(
                    "no current revision for attachment " "%s, skipping" % attachment.pk
                )
                continue

            # the revision we'll use for some minor metadata when creating the
            # attachment later
            revision = attachment.current_revision

            # get the list of documents that the attachment is contained in
            documents = Document.objects.filter(pk__in=document_pks).order_by("pk")

            # has the document that the attachment was originally uploaded to
            # already been found?
            original_document = None

            # let's see if there is an English document, chances are that's
            # what we want
            original_document = documents.filter(locale="en-US").first()
            if original_document is not None:
                # create the attachment and mark the original as found
                self.create_attachment(
                    original_document, attachment, revision, is_original=True,
                )

            # hm, no English document found, so let's just use the document
            # with the lowest ID, create the attachment, and move on
            if original_document is None:
                original_document = documents.first()
                if original_document is not None:
                    self.create_attachment(
                        original_document, attachment, revision, is_original=True,
                    )

            # now go through the rest of the bunch but ignore the original
            # document we already created an attachment for
            for rest_document in documents.iterator():
                if (
                    original_document is not None
                    and rest_document.pk == original_document.pk
                ):
                    continue
                self.create_attachment(
                    rest_document, attachment, revision, is_original=False,
                )

            # we failed, didn't find any document for this document
            if original_document is None:
                self.stderr.write(
                    "Cannot find document for " "attachment %s" % attachment.pk
                )

        # yada yada yada
        if self.attached:
            attached_list = get_text_list(self.attached, "and")
            if self.dry_run:
                self.stdout.write(
                    "Dry attached files to documents: " "%s" % attached_list
                )
            else:
                self.stdout.write("Attached files to documents: %s" % attached_list)
        else:
            self.stdout.write("Nothing to attach!")
