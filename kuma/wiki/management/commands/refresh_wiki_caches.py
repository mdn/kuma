"""
Refresh cached wiki data.

Run this periodically, it's useful for preventing redundant traffic between
Kuma and other services like Kumascript.
"""


import hashlib
import logging
import urllib.parse

import requests

from django.conf import settings
from django.core.cache import cache
from django.core.management.base import BaseCommand

from kuma.wiki.models import Document


PAGE_EXISTS_KEY_TMPL = getattr(
    settings, "wiki_page_exists_key_tmpl", "kuma:page_exists:%s"
)
PAGE_EXISTS_TIMEOUT = getattr(settings, "wiki_page_exists_timeout", 86400)


class Command(BaseCommand):

    help = "Refresh cached wiki data"

    def add_arguments(self, parser):
        parser.add_argument("--baseurl", help="Base URL to site", default="")

    def handle(self, *args, **options):
        to_prefetch = []
        logging.info("Querying all Documents...")
        doc_cnt, doc_total = 0, Document.objects.count()
        for doc in Document.objects.order_by("-modified").iterator():

            # Give some indication of progress, occasionally
            doc_cnt += 1
            if (doc_cnt % 5000) == 0:
                logging.info("\t(%s / %s)" % (doc_cnt, doc_total))

            url = doc.get_absolute_url()
            if 'class="noinclude"' in doc.html:
                # A page containing class="noinclude" is very likely to be used
                # as included content on another page, so better prefetch. But,
                # prefetching templates won't help us, since they don't get
                # pre-processed by kumascript.
                to_prefetch.append(url)

            # Get an MD5 hash of the lowercased path
            path = doc.slug.lower().encode()
            path_hash = hashlib.md5(path).hexdigest()

            # Warm up the page_exists cache
            key = PAGE_EXISTS_KEY_TMPL % path_hash
            cache.set(key, 1, PAGE_EXISTS_TIMEOUT)

        # Now, prefetch all the documents flagged in need in the previous loop.
        pre_total, pre_cnt = len(to_prefetch), 0
        logging.info("Prefetching %s documents..." % (len(to_prefetch)))
        for url in to_prefetch:
            full_url = urllib.parse.urljoin(options["baseurl"], url)
            try:
                pre_cnt += 1
                logging.info("\t(%s/%s) %s" % (pre_cnt, pre_total, full_url))
                requests.get(full_url)
            except Exception as e:
                logging.error("\t\tFAILED: %s; %s" % (full_url, e))
