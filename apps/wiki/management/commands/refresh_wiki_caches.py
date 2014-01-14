"""
Refresh cached wiki data.

Run this periodically, it's useful for preventing redundant traffic between
Kuma and other services like Kumascript.
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

from wiki.models import (Document, Revision)


PAGE_EXISTS_KEY_TMPL = getattr(settings, 'wiki_page_exists_key_tmpl',
                               'kuma:page_exists:%s')
PAGE_EXISTS_TIMEOUT = getattr(settings, 'wiki_page_exists_timeout',
                              86400)


class Command(BaseCommand):

    help = "Refresh cached wiki data"
    option_list = BaseCommand.option_list + (
        make_option('--baseurl', dest="baseurl",
                    default=False,
                    help="Base URL to site"),
    )

    def handle(self, *args, **options):
        
        base_url = options['baseurl']
        if not base_url:
            from django.contrib.sites.models import Site
            site = Site.objects.get_current()
            base_url = 'http://%s' % site.domain

        to_prefetch = []
        logging.info("Querying all Documents...")
        doc_cnt, doc_total = 0, Document.objects.count()
        for doc in Document.objects.order_by('-modified').iterator():

            # Give some indication of progress, occasionally
            doc_cnt += 1
            if (doc_cnt % 5000) == 0:
                logging.info("\t(%s / %s)" %
                             (doc_cnt, doc_total))

            url = doc.get_absolute_url()
            if 'class="noinclude"' in doc.html and not doc.is_template:
                # A page containing class="noinclude" is very likely to be used
                # as included content on another page, so better prefetch. But,
                # prefetching templates won't help us, since they don't get
                # pre-processed by kumascript.
                to_prefetch.append(url)

            # Get an MD5 hash of the lowercased path
            path = doc.full_path.lower().encode('utf-8')
            path_hash = hashlib.md5(path).hexdigest()

            # Warm up the page_exists cache
            key = PAGE_EXISTS_KEY_TMPL % path_hash
            cache.set(key, 1, PAGE_EXISTS_TIMEOUT)

        # Now, prefetch all the documents flagged in need in the previous loop.
        pre_total, pre_cnt = len(to_prefetch), 0
        logging.info("Prefetching %s documents..." % (len(to_prefetch)))
        for url in to_prefetch:
            full_url = urlparse.urljoin(options['baseurl'], url)
            try:
                pre_cnt += 1
                logging.info("\t(%s/%s) %s" % (pre_cnt, pre_total, full_url))
                requests.get(full_url)
            except Exception, e:
                logging.error("\t\tFAILED: %s; %s" % (full_url, e))
