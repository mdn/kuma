from django.core.management.base import NoArgsCommand
from django.utils.text import get_text_list

from ...models import Document


class Command(NoArgsCommand):
    help = "Populate m2m relations for documents and their attachments"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--dry-run',
                            action='store_true', dest='dry_run', default=False,
                            help="Do everything except actually populating "
                                 "the attachments.")

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        documents = (Document.admin_objects.filter(attachments_populated=False)
                                           .only('pk', 'html'))
        self.stdout.write("Populating document attachments "
                          "for %s documents...\n\n" % documents.approx_count())

        populated = []
        for document in documents.iter_smart(report_progress=True):
            if not dry_run:
                document.populate_attachments(update_populated_field=True)
            populated.append(document.pk)

        if populated:
            populated_list = get_text_list(populated, 'and')
            if dry_run:
                self.stdout.write('Dry populated attachments for documents: '
                                  '%s' % populated_list)
            else:
                self.stdout.write('Populated attachments for documents: %s' %
                                  populated_list)
        else:
            self.stdout.write('Nothing to populate!')
