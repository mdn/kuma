"""
Migration tool that copies pages from a MindTouch database to the Kuma wiki.

Should be idempotent - ie. running this repeatedly should result only in
updates, and not duplicate documents or repeated revisions.

TODO
* https://bugzilla.mozilla.org/show_bug.cgi?id=710713
* https://bugzilla.mozilla.org/showdependencytree.cgi?id=710713&hide_resolved=1
"""
import time
import datetime
from optparse import make_option

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, NoArgsCommand, CommandError
from django.db import connections, connection, transaction, IntegrityError
from django.utils import encoding, hashcompat

import commonware.log

from wiki.models import (Document, Revision, CATEGORIES, SIGNIFICANCES,
                         TitleCollision)

import wiki.content
from wiki.content import (SectionIDFilter, SECTION_EDIT_TAGS)

from dekicompat.backends import DekiUser, DekiUserBackend


log = commonware.log.getLogger('kuma.migration')

HISTORY_LIMIT = 100
ADMIN_ROLE_IDS = (4, )

class Command(BaseCommand):
    """Migrate wiki content from MindTouch to Kuma's wiki app"""

    def handle(self, *args, **options):
        log.info("Starting up")

        self.users = {}
        self.wikidb = connections['wikidb']
        self.cur = self.wikidb.cursor()

        pages_rows = []

        if True:
            # Grab the most viewed pages
            log.info("Migrating most viewed pages...")
            self.cur.execute("""
                SELECT p.*, pc.*
                FROM pages AS p, page_viewcount AS pc 
                WHERE 
                    pc.page_id=p.page_id AND
                    page_namespace = 0
                ORDER BY p.page_id ASC
                LIMIT 10
            """)
            pages_rows.extend(self._fetchallDicts(self.cur))

        if True:
            # Grab the most recently modified
            log.info("Migrating recently modified pages...")
            self.cur.execute("""
                SELECT *
                FROM pages
                WHERE page_namespace = 0
                ORDER BY page_id ASC
                LIMIT 10
            """)
            pages_rows.extend(self._fetchallDicts(self.cur))

        if True:
            # Grab the longest pages
            log.info("Migrating longest pages...")
            self.cur.execute("""
                SELECT * 
                FROM pages 
                WHERE page_namespace = 0
                ORDER BY page_id ASC
                LIMIT 10
            """)
            pages_rows.extend(self._fetchallDicts(self.cur))

        for r in pages_rows:
            self.updateDocumentFromPagesRow(r)

    def updateDocumentFromPagesRow(self, r):
        log.info("\t%s || %s" % (r['page_title'], r['page_display_name']))

        try:
            doc, created = Document.objects.get_or_create(
                slug = r['page_title'] or r['page_display_name'],
                title = r['page_display_name'],
                defaults = dict(
                    category=CATEGORIES[0][0]
                ))

            self.updateRevisions(r, doc)

            rev, created = Revision.objects.get_or_create(
                document = doc,
                # HACK: Using ID of -1 to indicate the current MindTouch
                # revision. All revisions of a Kuma document have revisions,
                # whereas MindTouch only tracks "old" revisions.
                mindtouch_old_id = -1,
                defaults = dict(
                    creator = self.getUserForPage(r),
                    is_approved = True,
                    significance = SIGNIFICANCES[0][0],
                ))

            rev.slug = r['page_title'] or r['page_display_name']
            rev.title = r['page_display_name']
            rev.content = r['page_text']
            rev.comment = r['page_comment']

            # Save, and force to current revision regardless of whatever the
            # highest revision ID might be.
            rev.save()
            rev.make_current()

            log.info("\t\t\t %s :: %s (%s)" % (rev.mindtouch_old_id, rev.pk, "CURRENT"))

        except TitleCollision, e:
            log.error('\t\tPROBLEM %s' % type(e))
        
    def updateRevisions(self, r_page, doc):
        log.info("\t\tUpdating revisions...")
        self.cur.execute("""
            SELECT *
            FROM old as o
            WHERE
                o.old_page_id = %s
            ORDER BY o.old_revision DESC
            LIMIT %s
        """, (
            r_page['page_id'],
            HISTORY_LIMIT,
        ))
        revs = sorted(self._fetchallDicts(self.cur),
                      key=lambda r: r['old_revision'])
        for r in revs:

            # HACK: Convert the flat timestamp into something pythonic
            ts = datetime.datetime.fromtimestamp(
                    time.mktime(time.strptime(r['old_timestamp'],
                                              "%Y%m%d%H%M%S")))
            # TODO: Timezone necessary here?

            rev, created = Revision.objects.get_or_create(
                document=doc,
                mindtouch_old_id=r['old_id'],
                defaults=dict(
                    slug = doc.slug,
                    title = doc.title,
                    creator = self.getUserForRevision(r),
                    is_approved = True,
                    significance = SIGNIFICANCES[0][0],
                    comment = r['old_comment'],
                    content = r['old_text'],
                    created = ts,
                    reviewed = ts,
                    reviewer = self.getSuperuser(),
                ))

            log.info("\t\t\t %s (%s) :: %s (%s)" % (r['old_id'], r['old_revision'], rev.pk, created))

    def getUserForPage(self, r):
        # return User.objects.filter(is_superuser=1)[0]
        # TODO: Get or create user corresponding to MT account
        return self.getDjangoUserforDekiUserID(r['page_user_id'])

    def getUserForRevision(self, r):
        # return User.objects.filter(is_superuser=1)[0]
        # TODO: Get or create user corresponding to MT account
        return self.getDjangoUserforDekiUserID(r['old_user'])

    def getDjangoUserforDekiUserID(self, deki_user_id):
        
        # If we don't already have this Deki user cached, look up or migrate
        if deki_user_id not in self.users:

            # Look up the user straight from the database
            self.cur.execute("""
                SELECT * 
                FROM users AS u
                WHERE
                    u.user_id = %s
            """, (deki_user_id,))
            r = list(self._fetchallDicts(self.cur))[0]
            deki_user = DekiUser(
                id = r['user_id'],
                username = r['user_name'],
                fullname = r['user_real_name'],
                email = r['user_email'],
                gravatar = '')

            # Scan user grants for admin roles to set Django flags.
            self.cur.execute("""
                SELECT *
                FROM user_grants AS ug
                WHERE
                    user_id = %s
            """, (deki_user_id,))
            is_admin = False
            for rg in self._fetchallDicts(self.cur):
                if rg['role_id'] in ADMIN_ROLE_IDS:
                    is_admin = True
            
            deki_user.is_superuser = deki_user.is_staff = is_admin

            # Finally get/create Django user and cache it.
            # FIXME: THIS NEGELCTS PASSWORD ON THE DJANGO SIDE! But, we're
            # probably okay, post-BrowserID
            user = DekiUserBackend.get_or_create_user(deki_user)
            self.users[deki_user_id] = user

        return self.users[deki_user_id]
    
    def getSuperuser(self):
        return User.objects.filter(is_superuser=1)[0]

    def _fetchallDicts(self, cursor):
        names = [x[0] for x in cursor.description]
        return (dict(zip(names, row))
                for row in cursor.fetchall())
