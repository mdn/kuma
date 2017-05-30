"""Common methods for scraping management commands."""
from argparse import ArgumentTypeError
import logging

from django.core.management.base import BaseCommand
from django.utils.six.moves.urllib.parse import urlparse

from kuma.scrape.scraper import Scraper


class ScrapeCommand(BaseCommand):
    """Common base class for scraping management commands."""
    def make_scraper(self, **options):
        """Create a Scraper instance for management commands."""
        return Scraper(**options)

    def parse_url_or_path(self, url_or_path):
        if url_or_path.startswith('http'):
            bits = urlparse(url_or_path)
            host = bits.netloc
            path = bits.path
            ssl = (bits.scheme == 'https')
        else:
            host = 'developer.mozilla.org'
            ssl = True
            path = url_or_path
        return host, ssl, path

    def setup_logging(self, verbosity):
        """Update logger for desired verbosity."""
        log_format = '%(levelname)s: %(message)s'
        log_name = 'kuma.scraper'
        console = logging.StreamHandler(self.stderr)

        if verbosity == 0:
            level = logging.WARNING
        elif verbosity == 1:  # default
            level = logging.INFO
        elif verbosity == 2:
            level = logging.DEBUG
        elif verbosity > 2:
            level = logging.DEBUG
            log_format = '%(name)s:%(levelname)s: %(message)s'
            log_name = ''

        formatter = logging.Formatter(log_format)
        console.setLevel(level)
        console.setFormatter(formatter)
        logger = logging.getLogger(log_name)
        logger.setLevel(level)
        logger.addHandler(console)

    def int_all_type(self, value):
        """A command argument that can take an integer or 'all'."""
        if value.strip().lower() == 'all':
            return 'all'
        try:
            as_int = int(value)
        except ValueError:
            msg = "%r should be 'all' or an integer" % value
            raise ArgumentTypeError(msg)
        return as_int
