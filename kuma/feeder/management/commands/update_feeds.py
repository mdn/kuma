

import logging
import time

from django.core.management.base import BaseCommand

from kuma.feeder.utils import update_feeds


class Command(BaseCommand):
    """Update all registered RSS/Atom feeds."""

    def add_arguments(self, parser):
        parser.add_argument(
            '--force', '-f',
            help='Fetch even disabled feeds.',
            action='store_true')

    def handle(self, *args, **options):
        """
        Locked command handler to avoid running this command more than once
        simultaneously.
        """
        force = options['force']
        verbosity = int(options['verbosity'])

        # Setup logging
        console = logging.StreamHandler(self.stderr)
        level = [logging.WARNING,
                 logging.INFO,
                 logging.DEBUG][min(verbosity, 2)]
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        console.setLevel(level)
        console.setFormatter(formatter)
        log = logging.getLogger('kuma.feeder')
        log.setLevel(level)
        log.addHandler(console)

        # Setup fetch
        log.info("Starting to fetch updated feeds")
        start = time.time()
        if force:
            log.info('--force option set: Trying to fetch all known feeds.')

        # Fetch feeds
        new_entry_count = update_feeds(force)
        log.info(
            f"Finished run in {time.time() - start:.2f} seconds "
            f"for {new_entry_count} new entries")
