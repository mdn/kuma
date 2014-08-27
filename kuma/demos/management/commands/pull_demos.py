import logging
from optparse import make_option

from django.core.management.base import BaseCommand

from demos.management.commands.migrate_demos import _disable_auto_date_fields
from demos.models import Submission

logger = logging.getLogger(__name__)


class Command(BaseCommand):

    option_list = BaseCommand.option_list + (
        make_option('--source', dest="source", default='old',
                    help="Source DATABASE from which to pull demos"),
        make_option('--dest', dest="dest", default='default',
                    help="Destination DATABASE to which to push demos"),
        make_option('--slug', dest="slug", default=None,
                    help="Migrate specific demo by slug"),
        make_option('--skip-actions', action="store_true",
                    dest="skip_actions", default=False,
                    help="Skip migrating individual action records"),
    )

    def handle(self, *fixture_labels, **options):
        source = options['source']
        dest = options['dest']
        if options['slug']:
            dest_demos = Submission.objects.using(dest).filter(
                                                        slug=options['slug'])
        else:
            dest_demos = Submission.objects.using(dest).all()
        logger.info("Pulling %s demo(s)" % len(dest_demos))
        for dest_demo in dest_demos:
            logger.info(dest_demo.slug)
            try:
                source_demo = Submission.objects.using(source).get(
                                                        slug=dest_demo.slug)
            except:
                # SubmissionManager filters out censored demos, don't bother
                # to pull a demo that's been censored
                continue
            _disable_auto_date_fields(dest_demo)
            dest_demo.modified = source_demo.modified
            dest_demo.launches.total = source_demo.launches.total
            dest_demo.launches.recent = source_demo.launches.recent
            dest_demo.likes.total = source_demo.likes.total
            dest_demo.likes.recent = source_demo.likes.recent
            dest_demo.save(using=dest)
