# encoding: utf-8
"""
Manually schedule the rendering of a document
"""
import datetime
import logging
from optparse import make_option

from django.core.management.base import BaseCommand, CommandError

from kuma.wiki.models import Document, DocumentRenderingInProgress
from kuma.wiki.tasks import render_document


class Command(BaseCommand):
    args = "<document_path document_path ...>"
    help = "Render a wiki document"
    option_list = BaseCommand.option_list + (
        make_option('--all', dest="all", default=False,
                    action="store_true",
                    help="Render ALL documents"),
        make_option('--min-age', dest="min_age", default=600,
                    help="Documents rendered less than this many seconds ago "
                         "will be skipped"),
        make_option('--baseurl', dest="baseurl",
                    default=False,
                    help="Base URL to site"),
        make_option('--force', action="store_true", dest="force",
                    default=False,
                    help="Force rendering, first clearing record of any "
                         "rendering in progress"),
        make_option('--nocache', action="store_true", dest="nocache",
                    default=False,
                    help="Use Cache-Control: no-cache instead of max-age=0"),
        make_option('--defer', action="store_true", dest="defer",
                    default=False,
                    help="Defer rendering"),
    )

    def handle(self, *args, **options):
        self.options = options

        self.base_url = options['baseurl']
        if not self.base_url:
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            self.base_url = 'http://%s' % site.domain

        if options['all']:
            logging.info(u"Querying ALL %s documents..." %
                         Document.objects.count())
            docs = Document.objects.order_by('-modified').iterator()
            for doc in docs:
                self.do_render(doc)

        else:
            if not len(args) == 1:
                raise CommandError("Need at least one document path to render")
            for path in args:
                # Accept a single page path from command line, but be liberal in
                # what we accept, eg: /en-US/docs/CSS (full path); /en-US/CSS (no
                # /docs); or even en-US/CSS (no leading slash)
                if path.startswith('/'):
                    path = path[1:]
                locale, sep, slug = path.partition('/')
                head, sep, tail = slug.partition('/')
                if head == 'docs':
                    slug = tail
                self.do_render(Document.objects.get(locale=locale, slug=slug))

    def do_render(self, doc):
        # Skip very recently rendered documents. This should help make it
        # easier to start and stop an --all command without needing to start
        # from the top of the list every time.
        if doc.last_rendered_at:
            now = datetime.datetime.now()
            render_age = now - doc.last_rendered_at
            min_age = datetime.timedelta(seconds=self.options['min_age'])
            if (render_age < min_age):
                logging.debug(u"Skipping %s (%s) - rendered %s sec ago" %
                              (doc, doc.get_absolute_url(), render_age))
                return

        if self.options['force']:
            doc.render_started_at = None

        if self.options['nocache']:
            cc = 'no-cache'
        else:
            cc = 'max-age=0'

        if self.options['defer']:
            logging.info(u"Queuing deferred render for %s (%s)" %
                          (doc, doc.get_absolute_url()))
            render_document.delay(doc.pk, cc, self.base_url)
            logging.debug(u"Queued.")

        else:
            logging.info(u"Rendering %s (%s)" %
                         (doc, doc.get_absolute_url()))
            try:
                render_document(doc, cc, self.base_url)
                logging.debug(u"DONE.")
            except DocumentRenderingInProgress:
                logging.error(u"Rendering is already in progress for this document")
