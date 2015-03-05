from django.core.management.base import NoArgsCommand

from kuma.wiki.models import Document


class Command(NoArgsCommand):
    help = "Populate m2m relations for documents and their attachments"

    def handle(self, *args, **options):
        for doc in Document.objects.all():
            for attachment in doc.attachments:
                rev = attachment.current_revision
                attachment.attach(doc, rev.creator, rev.filename())
