"""
Refresh cached wiki data.

Run this periodically, it's useful for preventing redundant traffic between
Kuma and other services like Kumascript.
"""
import sys
import time
import datetime
import hashlib
import logging

from optparse import make_option

from django.conf import settings
from django.core.cache import cache
from django.contrib.auth.models import User
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
    )

    def handle(self, *args, **options):
        self.options = options

        logging.info("Querying all Documents...")
        doc_cnt, doc_total = 0, Document.objects.count()
        for doc in Document.objects.order_by('-modified').iterator():

            # Give some indication of progress, occasionally
            doc_cnt += 1
            if (doc_cnt % 1000) == 0:
                logging.info("(%s / %s) documents processed" %
                             (doc_cnt, doc_total))

            # Get an MD5 hash of the lowercased path
            path = doc.full_path.lower().encode('utf-8')
            path_hash = hashlib.md5(path).hexdigest()

            # Warm up the page_exists cache
            key = PAGE_EXISTS_KEY_TMPL % path_hash
            cache.set(key, 1, PAGE_EXISTS_TIMEOUT)
