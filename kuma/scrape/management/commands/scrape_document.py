"""Scrape a wiki document(s) from a Kuma website."""


from django.core.management.base import CommandError

from . import ScrapeCommand


class Command(ScrapeCommand):
    help = 'Scrape a wiki document.'

    def add_arguments(self, parser):
        """Add arguments for scraping an MDN wiki document."""
        parser.add_argument('urls',
                            metavar='URL_OR_PATH',
                            nargs='+',
                            help='URL or path to a wiki page')
        parser.add_argument('--force',
                            help='Update existing Document record',
                            action='store_true')
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
        for url in options['urls']:
            host, ssl, path = self.parse_url_or_path(url)
            scraper = self.make_scraper(host=host, ssl=ssl)

            params = {}
            for param in ('force', 'translations', 'revisions', 'depth'):
                if options[param]:
                    params[param] = options[param]
            scraper.add_source("document", path, **params)

            scraper.scrape()
            source = scraper.sources['document:' + path]
            if source.state == source.STATE_ERROR:
                raise CommandError('Unable to scrape document "%s".' % path)

            elif source.freshness == source.FRESH_NO and not options['force']:
                self.stderr.write('Document "%s" already exists. Use --force to update.' % path)
