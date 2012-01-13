"""
Migration tool that copies pages from a MindTouch database to the Kuma wiki.

Should be idempotent - ie. running this repeatedly should result only in
updates, and not duplicate documents or repeated revisions.

TODO
* https://bugzilla.mozilla.org/show_bug.cgi?id=710713
* https://bugzilla.mozilla.org/showdependencytree.cgi?id=710713&hide_resolved=1
* Performance metrics
    * documents and revisions per hour
    * estimated time to completion, given rate so far
* Document limit - eg. exit after X documents updated, not including skips.
    * Stick this in a shell script loop so that the script exits occasionally
      to free memory?
        * Need to figure out when we're done, then, though.
"""
import sys
import re
import time
import datetime
import itertools
from optparse import make_option

import html5lib
from html5lib.filters._base import Filter as html5lib_Filter
from pyquery import PyQuery as pq

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

        make_option('--wipe', action="store_true", dest="wipe", default=False,
                    help="Wipe all documents before migration"),
        
        make_option('--all', action="store_true", dest="all", default=False,
                    help="Migrate all documents"),
        make_option('--slug', dest="slug", default=None,
                    help="Migrate specific page by slug"),
        make_option('--revisions', dest="revisions", type="int", default=999,
                    help="Limit revisions migrated per document"),
        make_option('--viewed', dest="most_viewed", type="int", default=0,
                    help="Migrate # of most viewed documents"),
        make_option('--recent', dest="recent", type="int", default=0,
                    help="Migrate # of recently modified documents"),
        make_option('--longest', dest="longest", type="int", default=0,
                    help="Migrate # of longest documents"),

        make_option('--limit', dest="limit", type="int", default=99999,
                    help="Stop after a migrating a number of documents"),
        make_option('--skip', dest="skip", type="int", default=0,
                    help="Skip a number of documents for migration"),
        
        make_option('--update-revisions', action="store_true",
                    dest="update_revisions", default=False,
                    help="Force update to existing revisions"),
        make_option('--update-documents', action="store_true",
                    dest="update_documents", default=False,
                    help="Force update to existing documents"),

        make_option('--template-metrics', action="store_true",
                    dest="template_metrics", default=False,
                    help="Measure template usage, skip migration"),
        make_option('--list-full-template', action="store_true",
                    dest="list_full_template", default=False,
                    help="Print the full template call, rather than"
                         " just the method used"),
        
        make_option('--verbose', action='store_true', dest='verbose',
                    help="Produce verbose output"),)

    def handle(self, *args, **options):
        """Main driver for the command"""
        self.init(options)

        if self.options['wipe']:
            self.wipe_documents()

        rows = self.gather_pages()

        if options['template_metrics']:
            self.handle_template_metrics(rows)
        else:
            self.handle_migration(rows)

    def init(self, options):
        """Set up connections and options"""

        settings.DATABASES.update(settings.MIGRATION_DATABASES)
        settings.CACHE_BACKEND = 'dummy://'

        self.options = options
        self.admin_role_ids = (4,)
        self.user_ids = {}

        self.wikidb = connections['wikidb']
        self.cur = self.wikidb.cursor()

        self.kumadb = connections['default']

    def handle_migration(self, rows):
        self.docs_migrated = self.index_migrated_docs()
        log.info("Found %s docs already migrated" %
                 len(self.docs_migrated.values()))
        
        ct = 0
        for r in rows:
            try:
                if ct < self.options['skip']:
                    # Skip rows until past the option value
                    continue
                if self.update_document(r):
                    # Something was actually updated and not skipped
                    ct += 1
                if ct >= self.options['limit']:
                    log.info("Reached limit of %s documents migrated" %
                             self.options['limit'])
                    return
            except Exception, e:
                log.error("FAILURE %s" % type(e))

        if ct == 0:
            # If every document gathered for migration was skipped, then we
            # basically did nothing. Exit with status 1, so that any script
            # wrapping us in a loop knows that it can probably stop for awhile.
            sys.exit("No migrations performed")

    def handle_template_metrics(self, rows):
        """Parse out DekiScript template calls from pages"""
        # This regex seems to catch all the DekiScript calls
        fn_pat = re.compile('^([0-9a-zA-Z_\.]+)')
        wt_pat = re.compile(r"""^wiki.template\(["']([^'"]+)['"]""")

        # PROCESS ALL THE PAGES!
        for r in rows:

            if not r['page_text'].strip():
                # Page empty, so skip it.
                continue

            doc = pq(r['page_text'])
            spans = doc.find('span.script')
            for span in spans:
                src = unicode(span.text).strip()
                if self.options['list_full_template']:
                    print src.encode('utf-8')
                else:
                    if src.startswith('wiki.template'):
                        pat = wt_pat
                        m = pat.match(src)
                        if not m: continue
                        print (u"Template:%s" % m.group(1)).encode('utf-8')
                    else:
                        pat = fn_pat
                        m = pat.match(src)
                        if not m: continue
                        out = m.group(1)
                        if out.startswith('template.'):
                            out = out.replace('template.', 'Template:')
                        if out.startswith('Template.'):
                            out = out.replace('Template.', 'Template:')
                        if '.' not in out and 'Template:' not in out:
                            out = u'Template:%s' % out
                        print out.encode('utf-8')

    @transaction.commit_on_success
    def wipe_documents(self):
        """Delete all documents"""
        docs = Document.objects.all()
        ct = 0
        log.info("Deleting %s documents..." % len(docs))
        for d in docs:
            d.delete()
            ct += 1
            if 0 == (ct % 10):
                log.debug("\t%s deleted" % ct)

    def index_migrated_docs(self):
        """Build an index of Kuma docs already migrated, mapping Mindtouch page
        ID to document last-modified."""
        kc = self.kumadb.cursor()
        kc.execute("""
            SELECT mindtouch_page_id, id, modified
            FROM wiki_document
            WHERE mindtouch_page_id IS NOT NULL
        """)
        return dict((r[0], (r[1], r[2])) for r in kc)

    def gather_pages(self):
        """Gather rows for pages using the current options"""
        iters = []

        # TODO: Migrate pages from namespaces other than 0

        if self.options['all']:
            # Migrating all pages trumps any other criteria
            where = """
                WHERE page_namespace = 0
                ORDER BY page_timestamp DESC
            """
            self.cur.execute("SELECT count(*) FROM pages %s" % where)
            log.info("Gathering ALL %s pages from MindTouch..." %
                     self.cur.fetchone()[0])
            iters.append(self._query("SELECT * FROM pages %s" % where))

        elif self.options['slug']:
            # Migrating a single page...
            log.info("Searching for %s" % self.options['slug'])
            iters.append(self._query("""
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
                iters.append(self._query("""
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
                iters.append(self._query("""
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
                iters.append(self._query("""
                    SELECT * 
                    FROM pages 
                    WHERE page_namespace = 0
                    ORDER BY length(page_text) DESC
                    LIMIT %s
                """, self.options['longest']))

        return itertools.chain(*iters)

    @transaction.commit_on_success
    def update_document(self, r):
        """Update Kuma document from given MindTouch page record"""
        # Check to see if this doc has already been migrated, and if the
        # exising is doc is up to date.
        page_ts = self.parse_timestamp(r['page_timestamp'])
        last_mod = self.docs_migrated.get(r['page_id'], (None, None))[1]
        if (not self.options['update_documents'] and last_mod is not None 
                and last_mod >= page_ts):
            log.debug("\t%s (%s) up to date" %
                      (r['page_title'], r['page_display_name']))
            return False

        log.info("\t%s (%s)" % (r['page_title'], r['page_display_name']))

        try:
            # Ensure that the document exists, and has the MindTouch page ID
            slug = r['page_title'] or r['page_display_name']
            doc, created = Document.objects.get_or_create(slug=slug,
                title=r['page_display_name'], defaults=dict(
                    category=CATEGORIES[0][0],
                ))
            doc.mindtouch_page_id = r['page_id']

            if created:
                log.info("\t\tNew document created. (ID=%s)" % doc.pk)
            else:
                log.info("\t\tDocument already exists. (ID=%s)" % doc.pk)

            self.update_past_revisions(r, doc)
            self.update_current_revision(r, doc)

        except TitleCollision, e:
            log.error('\t\tPROBLEM %s' % type(e))
            return False

        return True

    def update_past_revisions(self, r_page, doc):
        """Update past revisions for the given page row and document"""
        ct_saved, ct_existing, ct_error = 0, 0, 0

        wc = self.wikidb.cursor()
        kc = self.kumadb.cursor()

        # Grab all the past revisions from MindTouch
        wc.execute("""
            SELECT * FROM old as o
            WHERE o.old_page_id = %s
            ORDER BY o.old_revision DESC
            LIMIT %s
        """, (r_page['page_id'], self.options['revisions'],))
        old_rows = sorted(self._query_dicts(wc),
                          key=lambda r: r['old_revision'], reverse=True)

        # Grab all the MindTouch old_ids from Kuma doc revisions
        kc.execute("""
            SELECT mindtouch_old_id, id
            FROM wiki_revision
            WHERE document_id=%s
        """, (doc.pk,))
        existing_old_ids = dict((r[0], r[1]) for r in kc)

        # Process all the past revisions...
        revs = []
        for r in old_rows:
        
            # Check if this already exists.
            existing_id = None
            if r['old_id'] in existing_old_ids:
                existing_id = existing_old_ids[r['old_id']]
                if not self.options['update_revisions']:
                    # If this revision has already been migrated, skip update.
                    ct_existing += 1
                    continue

            ts = self.parse_timestamp(r['old_timestamp'])
            rev_data = [
                doc.pk,
                r['old_id'], 1,
                doc.slug, doc.title,
                True, SIGNIFICANCES[0][0],
                '', '',
                r['old_text'], r['old_comment'],
                ts, self.get_django_user_id_for_deki_id(r['old_user']),
                ts, self.get_superuser_id()
            ]
            revs.append(rev_data)

            ct_saved += 1

        if len(revs):

            # Build SQL placeholders for the revisions
            row_placeholders = ",\n".join(
                "(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)"
                for x in revs)

            # Flatten list of revisions data in chronological order, so that we
            # get roughly time-sequential IDs and a flat list to fill the
            # placeholders.
            revs_flat = [col
                         for rev in sorted(revs, key=lambda x: x[11]) 
                         for col in rev]

            # Build and execute a giant query to save all the revisions.
            sql = """
                REPLACE INTO wiki_revision
                    (document_id,
                     mindtouch_old_id, is_mindtouch_migration,
                     slug, title,
                     is_approved, significance,
                     summary, keywords,
                     content, comment,
                     created, creator_id,
                     reviewed, reviewer_id)
                VALUES 
                %s
            """ % row_placeholders
            kc.execute(sql, revs_flat)

        log.info("\t\tPast revisions: %s saved, %s skipped, %s errors" %
                 (ct_saved, ct_existing, ct_error))

    def update_current_revision(self, r, doc):
        # HACK: Using old_id of None to indicate the current MindTouch revision.
        # All revisions of a Kuma document have revision records, whereas
        # MindTouch only tracks "old" revisions.
        rev, created = Revision.objects.get_or_create(document=doc,
            is_mindtouch_migration=True, mindtouch_old_id=None, defaults=dict(
                creator_id=self.get_django_user_id_for_deki_id(r['page_user_id']),
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

    def get_django_user_id_for_deki_id(self, deki_user_id):
        """Given a Deki user ID, come up with a Django user object whether we
        need to migrate it first or just fetch it."""
        # If we don't already have this Deki user cached, look up or migrate
        if deki_user_id not in self.user_ids:

            # Look up the user straight from the database
            self.cur.execute("SELECT * FROM users AS u WHERE u.user_id = %s",
                             (deki_user_id,))
            r = list(self._query_dicts(self.cur))[0]
            deki_user = DekiUser(id=r['user_id'], username=r['user_name'],
                                 fullname=r['user_real_name'],
                                 email=r['user_email'], gravatar='',)

            # Scan user grants for admin roles to set Django flags.
            self.cur.execute("""SELECT * FROM user_grants AS ug
                                WHERE user_id = %s""",
                             (deki_user_id,))
            is_admin = False
            for rg in self._query_dicts(self.cur):
                if rg['role_id'] in self.admin_role_ids:
                    is_admin = True
            deki_user.is_superuser = deki_user.is_staff = is_admin

            # Finally get/create Django user and cache it.
            user = DekiUserBackend.get_or_create_user(deki_user)
            self.user_ids[deki_user_id] = user.pk

        return self.user_ids[deki_user_id]

    SUPERUSER_ID = None
    def get_superuser_id(self):
        """Get the first superuser from Django we can find."""
        if not self.SUPERUSER_ID:
            self.SUPERUSER_ID = User.objects.filter(is_superuser=1)[0].pk
        return self.SUPERUSER_ID

    def parse_timestamp(self, ts):
        """HACK: Convert a MindTouch timestamp into something pythonic"""
        # TODO: Timezone necessary here?
        dt = datetime.datetime.fromtimestamp(
                    time.mktime(time.strptime(ts, "%Y%m%d%H%M%S")))
        return dt

    def _query(self, sql, *params):
        self.cur.execute(sql, params)
        return self._query_dicts(self.cur)

    def _query_dicts(self, cursor):
        """Wrapper for cursor.fetchall() that uses the cursor.description to
        convert each row's list of columns to a dict."""
        names = [x[0] for x in cursor.description]
        return (dict(zip(names, row)) for row in cursor)
