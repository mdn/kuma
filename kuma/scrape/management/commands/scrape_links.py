"""Scrape document links found on a MDN page, so that all the links will work."""


from django.core.management.base import CommandError

from . import ScrapeCommand


class Command(ScrapeCommand):
    help = 'Scrape the pages linked from a page (default homepage).'

    def add_arguments(self, parser):
        """Add common arguments for scraping MDN."""
        parser.add_argument('url',
                            metavar='URL_OR_PATH',
                            nargs='?',
                            default='https://wiki.developer.mozilla.org/en-US/',
                            help='URL or path to a wiki page')
        parser.add_argument('--revisions',
                            dest='revisions',
                            metavar='REVS', type=int, default=1,
                            help='Depth in revision history to scrape')
        parser.add_argument('--translations',
                            help='Include translations',
                            action='store_true',
                            dest='translations')
        parser.add_argument('--depth',
                            dest='depth',
                            metavar='DEPTH', type=self.int_all_type, default=0,
                            help=('Depth in the topic tree to scrape'
                                  ' ("all" for all)'))

    def handle(self, *arg, **options):
        self.setup_logging(options['verbosity'])
        host, ssl, path = self.parse_url_or_path(options['url'])
        scraper = self.make_scraper(host=host, ssl=ssl)

        params = {}
        for param in ('translations', 'revisions', 'depth'):
            if options[param]:
                params[param] = options[param]
        scraper.add_source("links", path, **params)

        scraper.scrape()
        source = scraper.sources['links:' + path]
        if source.state == source.STATE_ERROR:
            raise CommandError('Unable to scrape links on "%s".' % path)
