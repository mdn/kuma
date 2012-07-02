
"""
Manually schedule the rendering of a document
"""
import sys
import time
import datetime
import urlparse
import hashlib
import logging
import requests

from optparse import make_option

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
from django.contrib.sites.models import Site
from django.core.management.base import (BaseCommand, NoArgsCommand,
                                         CommandError)

from wiki.models import (Document, Revision,
                         DocumentRenderingInProgress)
from wiki.tasks import render_document


class Command(BaseCommand):

    help = "Render a wiki document"
    option_list = BaseCommand.option_list + (
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
        
        base_url = options['baseurl']
        if not base_url:
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            base_url = 'http://%s' % site.domain

        path = args[0]
        if path.startswith('/'):
            path = path[1:]
        locale, sep, slug = path.partition('/')
        head, sep, tail = slug.partition('/')
        if head == 'docs':
            slug = tail

        doc = Document.objects.get(locale=locale, slug=slug)

        if options['force']:
            doc.render_started_at = None

        if options['nocache']:
            cc = 'no-cache'
        else:
            cc = 'max-age=0'

        if options['defer']:
            logging.info("Queuing deferred render for %s (%s)" %
                          (doc, doc.get_absolute_url()))
            render_document.delay(doc, cc, base_url)
            logging.info("Queued.")

        else:
            logging.info("Rendering %s (%s)" %
                         (doc, doc.get_absolute_url()))
            try:
                render_document(doc, cc, base_url)
                logging.info("DONE.")
            except DocumentRenderingInProgress:
                logging.error("Rendering is already in progress for this "
                              "document") 
