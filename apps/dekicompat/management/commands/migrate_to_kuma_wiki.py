"""
Migration tool that copies pages from a MindTouch database to the Kuma wiki.

Should be idempotent - ie. running this repeatedly should result only in
updates, and not duplicate documents or repeated revisions.

TODO
* https://bugzilla.mozilla.org/show_bug.cgi?id=710713
* https://bugzilla.mozilla.org/showdependencytree.cgi?id=710713&hide_resolved=1
"""
from optparse import make_option

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from django.db import connections, connection, transaction, IntegrityError
from django.utils import encoding, hashcompat

import commonware.log

from wiki.models import (Document, Revision, CATEGORIES, SIGNIFICANCES)

import wiki.content
from wiki.content import (SectionIDFilter, SECTION_EDIT_TAGS)


log = commonware.log.getLogger('kuma.migration')


class Command(BaseCommand):
    """Migrate wiki content from MindTouch to Kuma's wiki app"""

    def handle(self, *args, **options):
        log.info("Starting up")

        wikidb = connections['wikidb']
        cur = wikidb.cursor()

        # Grab the most viewed pages
        log.info("Migrating most viewed pages...")
        cur.execute("""
            SELECT p.*, pc.*
            FROM pages AS p, page_viewcount AS pc 
            WHERE 
                pc.page_id=p.page_id AND
                page_namespace = 0
            ORDER BY pc.page_counter DESC
            LIMIT 25
        """)
        for r in self._fetchallDicts(cur):
            self.updateDocFromPagesRow(r)

        # Grab the most recently modified
        log.info("Migrating recently modified pages...")
        cur.execute("""
            SELECT *
            FROM pages
            WHERE page_namespace = 0
            ORDER BY page_timestamp DESC
            LIMIT 25
        """)
        for r in self._fetchallDicts(cur):
            self.updateDocFromPagesRow(r)

        # Grab the longest pages
        log.info("Migrating longest pages...")
        cur.execute("""
            SELECT * 
            FROM pages 
            WHERE page_namespace = 0
            ORDER BY length(page_text) DESC
            LIMIT 25
        """)
        for r in self._fetchallDicts(cur):
            self.updateDocFromPagesRow(r)

    def updateDocFromPagesRow(self, r):
        log.info("\t%s || %s" % (r['page_title'], r['page_display_name']))

        try:
            doc, created = Document.objects.get_or_create(
                slug=r['page_title'],
                title=r['page_display_name'],
                defaults=dict(
                    category=CATEGORIES[0][0]
                ))

            if not doc.current_revision:
                rev = Revision(document=doc)
            else:
                rev = doc.current_revision

            rev.slug = r['page_title']
            rev.title = r['page_display_name']
            rev.content = r['page_text']
            
            rev.creator = self.getUserForPage(r)
            rev.approved = True
            rev.significance = SIGNIFICANCES[0][0]
            rev.comment = r['page_comment']

            rev.save()

        except Exception, e:
            log.error('\t\tPROBLEM %s' % type(e))
        
    def getUserForPage(self, r):
        # TODO: Get or create user corresponding to MT account
        return User.objects.filter(is_superuser=1)[0]

    def _fetchallDicts(self, cursor):
        names = [x[0] for x in cursor.description]
        return (dict(zip(names, row))
                for row in cursor.fetchall())
