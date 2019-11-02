

import json

from django.core.management.base import CommandError

from kuma.scrape.fixture import FixtureLoader

from . import ScrapeCommand


class Command(ScrapeCommand):
    help = 'Sample data from a running MDN server.'

    def add_arguments(self, parser):
        parser.add_argument('spec',
                            metavar='specification.json',
                            help='Sample specification file')
        parser.add_argument('--host',
                            help=('Where to sample MDN from (default'
                                  ' "wiki.developer.mozilla.org")'),
                            default='wiki.developer.mozilla.org')
        parser.add_argument('--nossl',
                            help='Disable SSL',
                            action='store_false',
                            default='true',
                            dest='ssl')
        parser.add_argument('--force',
                            help='Update existing records',
                            action='store_true')

    def handle(self, *arg, **options):
        self.setup_logging(options['verbosity'])
        host = options['host']
        ssl = options['ssl']
        force = options['force']
        scraper = self.make_scraper(host=host, ssl=ssl)
        with open(options['spec']) as spec_file:
            data = json.load(spec_file)

        # Load fixtures, which may include flags and settings
        fl = FixtureLoader(data.get('fixtures', {}))
        fl.load()

        # Scrape data from MDN
        for source_spec in data.get('sources', []):
            source_name, param, source_args = source_spec
            if force:
                source_args['force'] = True
            scraper.add_source(source_name, param, **source_args)
        sources = scraper.scrape()
        incomplete = 0
        for name, source in sources.items():
            if source.state != source.STATE_DONE:
                if hasattr(source, 'error'):
                    err = ' "%s"' % source.error
                else:
                    err = ''
                self.stderr.write("%s: %s%s\n" % (name, source.state, err))
                incomplete += 1
        if incomplete:
            raise CommandError("%d source%s incomplete." %
                               (incomplete, '' if incomplete == 1 else 's'))
