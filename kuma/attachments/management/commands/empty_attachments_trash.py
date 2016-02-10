from datetime import date, timedelta

from constance import config
from django.core.management.base import NoArgsCommand
from django.utils.text import get_text_list

from ...models import TrashedAttachment


class Command(NoArgsCommand):
    help = "Empty the attachments trash"

    def add_arguments(self, parser):
        parser.add_argument('-n', '--dry-run',
                            action='store_true', dest='dry_run', default=False,
                            help="Do everything except actually emptying the "
                                 "trash.")

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        timeframe = timedelta(days=config.WIKI_ATTACHMENTS_KEEP_TRASHED_DAYS)
        trashed_attachments = TrashedAttachment.objects.filter(
            trashed_at__lte=date.today() - timeframe
        )
        self.stdout.write('Emptying attachments trash '
                          'for %s attachments...\n\n' %
                          trashed_attachments.approx_count())

        deleted = []
        # in case we have lots of attachments we don't want Django's
        # queryset iteration to break the deletion
        for attachment in trashed_attachments.iter_smart(report_progress=True):
            deleted.append(attachment.file.name)
            if not dry_run:
                attachment.delete()

        if deleted:
            deleted_list = get_text_list(deleted, 'and')
            if dry_run:
                self.stdout.write('Dry deleted the following files: %s' %
                                  deleted_list)
            else:
                self.stdout.write('Deleted the following files: %s' %
                                  deleted_list)
        else:
            self.stdout.write('Nothing to delete!')
