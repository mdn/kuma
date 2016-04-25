from datetime import timedelta
from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from kuma.spam.akismet import Akismet, AkismetError
from kuma.wiki.forms import AkismetHistoricalData
from kuma.wiki.models import (Document, DocumentDeletionLog,
                              RevisionAkismetSubmission)


class Command(BaseCommand):
    help = ("Seed Akismet spam with documents that were deleted "
            "because they were spam")

    def add_arguments(self, parser):
        # Positional arguments
        parser.add_argument(
            'username',
            action='store',
            type=str,
            help='The username to save as the submission sender.'
        )
        parser.add_argument(
            '-n', '--dry-run',
            action='store_true',
            dest='dry_run',
            default=False,
            help='Do everything except actually submit.',
        )
        parser.add_argument(
            '-d', '--days',
            action='store',
            dest='days',
            default=365,
            type=int,
            help='Number of days of deletion logs to inspect.',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        # first get the deleted document logs for the last n days
        ttl = timezone.now() - timedelta(days=options['days'])
        logged_deletions = DocumentDeletionLog.objects.filter(
            # They use "spam"
            # deleting spam revisions;
            # the spam makes me cry.  -- willkg
            timestamp__gte=ttl,
            reason__icontains='spam'
        )
        count = logged_deletions.count()
        self.stdout.write('Checking %s deleted document logs' % count)

        sender = get_user_model().objects.get(username=options['username'])
        self.stdout.write(u'Submitting spam to Akismet as user %s' % sender)

        akismet = Akismet()

        if not akismet.ready:
            raise CommandError('Akismet client is not ready')

        for i, logged_deletion in enumerate(logged_deletions.iterator(), 1):
            self.stdout.write('%d/%d: ' % (i, count), ending='')
            # get the deleted document in question
            document = Document.admin_objects.filter(
                locale=logged_deletion.locale,
                slug=logged_deletion.slug,
            ).first()

            if document is None:
                # no document found with that locale and slug,
                # probably purged at some point
                self.stderr.write(u'Ignoring locale %s and slug %s' %
                                  (logged_deletion.locale,
                                   logged_deletion.slug))
                continue

            if not document.deleted:
                # guess the document got undeleted at some point again,
                # ignoring..
                self.stderr.write(u'Ignoring undeleted document %s' % document)
                continue

            if not document.current_revision:
                # no current revision found, which means something is fishy
                # but we can't submit it as spam since we don't have a revision
                self.stderr.write(u'Ignoring document %s without current '
                                  u'revision' % document.pk)
                continue

            akismet_data = AkismetHistoricalData(document.current_revision)
            params = akismet_data.parameters
            if dry_run:
                # we're in dry-run, so let's continue okay?
                self.stdout.write(u'Not submitting current revision %s of '
                                  u'document %s because of dry-mode' %
                                  (document.current_revision.pk, document.pk))
                continue
            try:
                akismet.submit_spam(**params)
            except AkismetError as exc:
                self.stderr.write(u'Akismet error while submitting current '
                                  u'revision %s of document %s: %s' %
                                  (document.current_revision.pk, document.pk,
                                   exc.debug_help))
            else:
                self.stdout.write(u'Successfully submitted current '
                                  u'revision %s of document %s' %
                                  (document.current_revision.pk, document.pk))
                submission = RevisionAkismetSubmission(
                    revision=document.current_revision,
                    sender=sender,
                    type=RevisionAkismetSubmission.SPAM_TYPE,
                )
                submission.save()
