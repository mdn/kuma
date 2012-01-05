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
from django.core.management.base import (BaseCommand, NoArgsCommand,
                                         CommandError)
from django.db import connections, connection, transaction, IntegrityError
from django.utils import encoding, hashcompat

import commonware.log

from wiki.models import (Document, Revision, CATEGORIES, SIGNIFICANCES,
                         TitleCollision)

import wiki.content
from wiki.content import (SectionIDFilter, SECTION_EDIT_TAGS)

from dekicompat.backends import DekiUser, DekiUserBackend


log = commonware.log.getLogger('kuma.migration')


class Command(BaseCommand):
    help = """Migrate content from MindTouch to Kuma"""

    option_list = BaseCommand.option_list + (
        make_option('--all', action="store_true", dest="all", default=False,
                    help="Migrate all documents"),
        make_option('--slug', dest="slug", default=None,
                    help="Migrate specific page by slug"),
        make_option('--revisions', dest="revisions", type="int", default=25,
                    help="Limit revisions migrated per document"),
        make_option('--viewed', dest="most_viewed", type="int", default=25,
                    help="Migrate # of most viewed documents"),
        make_option('--recent', dest="recent", type="int", default=25,
                    help="Migrate # of recently modified documents"),
        make_option('--longest', dest="longest", type="int", default=25,
                    help="Migrate # of longest documents"),
        make_option('--verbose', action='store_true', dest='verbose',
                    help="Produce verbose output"),)

    def handle(self, *args, **options):
        self.options = options
        self.admin_role_ids = (4,)
        self.users = {}
        self.wikidb = connections['wikidb']
        self.cur = self.wikidb.cursor()

        rows = self.gather_pages()
        log.info("Migrating %s pages to Kuma..." % len(rows))
        for r in rows:
            self.update_document(r)

    def gather_pages(self):
        """Gather rows for pages using the current options"""
        rows = []

        # TODO: Migrate pages from namespaces other than 0

        if self.options['all']:
            # Migrating all pages trumps any other criteria
            log.info("Gathering ALL pages from MindTouch...")
            rows.extend(self._fetchall_sql("""
                SELECT *
                FROM pages
                WHERE page_namespace = 0
                ORDER BY page_timestamp DESC
            """))

        elif self.options['slug']:
            # Migrating a single page...
            log.info("Searching for %s" % self.options['slug'])
            rows.extend(self._fetchall_sql("""
                SELECT *
                FROM pages
                WHERE
                    page_namespace = 0 AND
                    page_title = %s
                ORDER BY page_timestamp DESC
            """, self.options['slug']))

        else:

            if self.options['most_viewed'] > 0:
                # Grab the most viewed pages
                log.info("Gathering %s most viewed pages from MindTouch..." %
                         self.options['most_viewed'])
                rows.extend(self._fetchall_sql("""
                    SELECT p.*, pc.*
                    FROM pages AS p, page_viewcount AS pc 
                    WHERE 
                        pc.page_id=p.page_id AND
                        page_namespace = 0
                    ORDER BY pc.page_counter DESC
                    LIMIT %s
                """, self.options['most_viewed']))

            if self.options['recent'] > 0:
                # Grab the most recently modified
                log.info("Gathering %s recently modified pages from MindTouch..." %
                         self.options['recent'])
                rows.extend(self._fetchall_sql("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace = 0
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """, self.options['recent']))

            if self.options['longest'] > 0:
                # Grab the longest pages
                log.info("Gathering %s longest pages from MindTouch..." %
                         self.options['longest'])
                rows.extend(self._fetchall_sql("""
                    SELECT * 
                    FROM pages 
                    WHERE page_namespace = 0
                    ORDER BY length(page_text) DESC
                    LIMIT %s
                """, self.options['longest']))

        return rows

    def update_document(self, r):
        log.info("\t%s (%s)" % (r['page_title'], r['page_display_name']))

        try:
            slug = r['page_title'] or r['page_display_name']
            doc, created = Document.objects.get_or_create(slug=slug,
                title=r['page_display_name'], defaults=dict(
                    category=CATEGORIES[0][0]
                ))

            if created:
                log.info("\t\tNew document created. (ID=%s)" % doc.pk)
            else:
                log.info("\t\tDocument already exists. (ID=%s)" % doc.pk)

            self.update_past_revisions(r, doc)
            self.update_current_revision(r, doc)

        except TitleCollision, e:
            log.error('\t\tPROBLEM %s' % type(e))

    def update_past_revisions(self, r_page, doc):
        """Update past revisions for the given page row and document"""
        ct_new, ct_existing = 0, 0
        self.cur.execute("""
            SELECT *
            FROM old as o
            WHERE
                o.old_page_id = %s
            ORDER BY o.old_revision DESC
            LIMIT %s
        """, (r_page['page_id'], self.options['revisions'],))
        revs = sorted(self._fetchall_dicts(self.cur),
                      key=lambda r: r['old_revision'])
        for r in revs:

            ts = self.parse_timestamp(r['old_timestamp'])

            rev, created = Revision.objects.get_or_create(document=doc,
                mindtouch_old_id=r['old_id'], defaults=dict(
                    slug=doc.slug, title=doc.title,
                    creator=self.get_user_for_deki_id(r['old_user']),
                    is_approved=True,
                    significance=SIGNIFICANCES[0][0],
                    content=r['old_text'], comment=r['old_comment'],
                    created=ts, reviewed=ts,
                    reviewer=self.get_superuser(),))

            if created:
                ct_new += 1
            else:
                ct_existing += 1

        log.info("\t\tPast revisions: %s new, %s existing" %
                 (ct_new, ct_existing))

    def update_current_revision(self, r, doc):
        # HACK: Using ID of -1 to indicate the current MindTouch revision.
        # All revisions of a Kuma document have revision records, whereas
        # MindTouch only tracks "old" revisions.
        rev, created = Revision.objects.get_or_create(document=doc,
            mindtouch_old_id=-1, defaults=dict(
                creator=self.get_user_for_deki_id(r['page_user_id']),
                is_approved=True,
                significance=SIGNIFICANCES[0][0],))

        # Check to see if the current revision is up to date, in which case we
        # can skip the update and save a little time.
        page_ts = self.parse_timestamp(r['page_timestamp'])
        if not created and page_ts <= rev.created:
            log.info("\t\tCurrent revision already up to date. (ID=%s)" % rev.pk)
            return

        rev.created = rev.reviewed = page_ts
        rev.slug = r['page_title'] or r['page_display_name']
        rev.title = r['page_display_name']
        rev.content = r['page_text']
        rev.comment = r['page_comment']

        # Save, and force to current revision.
        rev.save()
        rev.make_current()

        if created:
            log.info("\t\tCurrent revision created. (ID=%s)" % rev.pk)
        else:
            log.info("\t\tCurrent revision updated. (ID=%s)" % rev.pk)

    def get_user_for_deki_id(self, deki_user_id):
        """Given a Deki user ID, come up with a Django user object whether we
        need to migrate it first or just fetch it."""
        # If we don't already have this Deki user cached, look up or migrate
        if deki_user_id not in self.users:

            # Look up the user straight from the database
            self.cur.execute("SELECT * FROM users AS u WHERE u.user_id = %s",
                             (deki_user_id,))
            r = list(self._fetchall_dicts(self.cur))[0]
            deki_user = DekiUser(id=r['user_id'], username=r['user_name'],
                                 fullname=r['user_real_name'],
                                 email=r['user_email'], gravatar='',)

            # Scan user grants for admin roles to set Django flags.
            self.cur.execute("""SELECT * FROM user_grants AS ug
                                WHERE user_id = %s""",
                             (deki_user_id,))
            is_admin = False
            for rg in self._fetchall_dicts(self.cur):
                if rg['role_id'] in self.admin_role_ids:
                    is_admin = True
            deki_user.is_superuser = deki_user.is_staff = is_admin

            # Finally get/create Django user and cache it.
            user = DekiUserBackend.get_or_create_user(deki_user)
            self.users[deki_user_id] = user

        return self.users[deki_user_id]

    def get_superuser(self):
        """Get the first superuser from Django we can find."""
        return User.objects.filter(is_superuser=1)[0]

    def parse_timestamp(self, ts):
        """HACK: Convert a MindTouch timestamp into something pythonic"""
        # TODO: Timezone necessary here?
        dt = datetime.datetime.fromtimestamp(
                    time.mktime(time.strptime(ts, "%Y%m%d%H%M%S")))
        return dt

    def _fetchall_sql(self, sql, *params):
        self.cur.execute(sql, params)
        return self._fetchall_dicts(self.cur)

    def _fetchall_dicts(self, cursor):
        """Wrapper for cursor.fetchall() that uses the cursor.description to
        convert each row's list of columns to a dict."""
        names = [x[0] for x in cursor.description]
        return (dict(zip(names, row))
                for row in cursor.fetchall())
