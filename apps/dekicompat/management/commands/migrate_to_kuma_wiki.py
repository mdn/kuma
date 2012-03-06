"""
Migration tool that copies pages from a MindTouch database to the Kuma wiki.

Should be idempotent - ie. running this repeatedly should result only in
updates, and not duplicate documents or repeated revisions.

TODO
* https://bugzilla.mozilla.org/show_bug.cgi?id=710713
* https://bugzilla.mozilla.org/showdependencytree.cgi?id=710713&hide_resolved=1
"""
import sys
import re
import time
import datetime
import itertools
import hashlib
from optparse import make_option

from BeautifulSoup import BeautifulSoup
from pyquery import PyQuery as pq

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import (BaseCommand, NoArgsCommand,
                                         CommandError)
import django.db
from django.db import connections, connection, transaction, IntegrityError
from django.utils import encoding, hashcompat

import commonware.log

from sumo.urlresolvers import reverse

from wiki.models import (Document, Revision, CATEGORIES, SIGNIFICANCES)

import wiki.content
from wiki.models import REDIRECT_CONTENT
from wiki.content import (SectionIDFilter, SECTION_EDIT_TAGS)

from dekicompat.backends import DekiUser, DekiUserBackend


log = commonware.log.getLogger('kuma.migration')

# Regular expression to match and extract page title from MindTouch redirects
# eg. #REDIRECT [[en/DOM/Foo]], #REDIRECT[[foo_bar_baz]]
MT_REDIR_PAT = re.compile(r"""^#REDIRECT ?\[\[([^\]]+)\]\]""")

# See also: https://github.com/mozilla/kuma/blob/mdn/apps/devmo/models.py#L327
# I'd just import from there, but wanted to do this a little differently
MT_NAMESPACES = (
    ('', 0),
    ('Talk:', 1),
    ('User:', 2),
    ('User_talk:', 3),
    ('Project:', 4),
    ('Project_talk:', 5),

    ('Help:', 12),
    ('Help_talk:', 13),
    ('Special:', -1),
    ('Template:', 10),
    ('Template_talk:', 11),
)
MT_NS_NAME_TO_ID = dict(MT_NAMESPACES)
MT_NS_ID_TO_NAME = dict((x[1], x[0]) for x in MT_NAMESPACES)
MT_MIGRATED_NS_IDS = (MT_NS_NAME_TO_ID[x] for x in (
    '', 'Talk:', 'User:', 'User_talk:', 'Project:', 'Project_talk:'
))

# NOTE: These are MD5 hashes of garbage User page content. The criteria is that
# the content was found to repeat more than 3 times, and was hand-reviewed by
# lorchard who determined they were MindTouch default content. Blame him if
# it's an overenthusiastic list.
#
# See also these SQL queries:
# https://bugzilla.mozilla.org/show_bug.cgi?id=710753#c3
# https://bugzilla.mozilla.org/show_bug.cgi?id=710753#c4
#
# And, see also this MySQL transcript listing the content involved:
# https://bugzilla.mozilla.org/attachment.cgi?id=590867

USER_NS_EXCLUDED_CONTENT_HASHES = """
7479e8f30d5ab0e9202195a1bddec69d
698141d0c92776d60d884ebce6d64d82
ca0c3622cdb213281cf2dc698b15c357
ce33312f48b8ce8a68c587173e276f3a
9ba3b75ba5e3ba82cfad83a50186ab35
e931344938b19ea93865568712c2b2de
a40f1d06233eef791bcf8b55df46cace
14d2e3e51d704084503f67eaaf47dc72
d41d8cd98f00b204e9800998ecf8427e
74ced08578951e424aff4e7a90f2b48b
55abb153d6e5d1bc22dae9938074f38d
43d1c34c5556ebf12e9d0601863eb752
f53c0981035e2378c8e8692a1e7f9649
68b329da9893e34099c7d8ad5cb9c940
8766b3552715bed94c106f6824efb535
7dbb4512068edc202eda2b853c415cb7
63f484aade7cfab43340bd001370c132
f71abdf1a61d4fbcf7a96c484f602434
baf848927342e7fa737b14277fa566f8
83c7ff527035fe0dd78c2330e08d6747
b43e15a05b457a6b79a5c553e0fbd9a7
3c9a42e7646f29f7c983fd0a8be88ecd
c2346672e9d426b4b8cac99507220a14
42c76681cb99f161fecccd2c1e56b4b0
3e31c2cafadd3ec47a88d0fc446bb929
0356162b5f5fc96b8d96222a839d05ec
""".split("\n")

# List of MindTouch locales mapped to Kuma locales.
MT_TO_KUMA_LOCALE_MAP = getattr(settings, 'MT_TO_KUMA_LOCALE_MAP')


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
        make_option('--redirects', dest="redirects", type="int", default=0,
                    help="Migrate # of documents containing redirects"),
        make_option('--nonen', dest="nonen", type="int", default=0,
                    help="Migrate # of documents in locales other than en-US"),

        make_option('--limit', dest="limit", type="int", default=99999,
                    help="Stop after a migrating a number of documents"),
        make_option('--skip', dest="skip", type="int", default=0,
                    help="Skip a number of documents for migration"),

        make_option('--maxlength', dest="maxlength", type="int",
                    default=1000000,
                    help="Maximum character length for page content"),

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

        make_option('--failfast', action='store_true', dest='failfast',
                    help="Do not trap exceptions; raise and exit errors"),
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

        start_ts = ts_now = time.time()

        self.rev_ct = 0
        ct, skip_ct, error_ct = 0, 0, 0

        for r in rows:
            try:
                if ct < self.options['skip']:
                    # Skip rows until past the option value
                    continue
                if self.update_document(r):
                    # Something was actually updated and not skipped
                    ct += 1
                else:
                    # This was a skip.
                    skip_ct += 1

                # Free memory in query cache after each document.
                django.db.reset_queries()

                if ct >= self.options['limit']:
                    log.info("Reached limit of %s documents migrated" %
                             self.options['limit'])
                    break

            except Exception, e:
                if self.options['failfast']:
                    # If the option is set, then just bail out.
                    raise
                else:
                    # Note: This traps *all* errors, so that the migration can get
                    # through what it can. This should really produce a problem
                    # documents report, though.
                    log.error('\t\tPROBLEM %s' % type(e))
                    error_ct += 1

            ts_now = time.time()
            duration = ts_now - start_ts
            total_ct = ct + skip_ct + error_ct
            if (total_ct % 10) == 0:
                log.info("Rate: %s docs/sec, %s secs/doc, "
                         "%s total in %s seconds" %
                         ((total_ct + 1) / (duration + 1),
                          (duration + 1) / (total_ct + 1),
                          total_ct, duration))
                log.info("Rate: %s revs/sec, %s total in %s seconds" %
                         ((self.rev_ct + 1) / (duration + 1),
                          self.rev_ct, duration))

        log.info("Migration finished: %s seconds, %s migrated, "
                 "%s skipped, %s errors" %
                 ((time.time() - start_ts), ct, skip_ct, error_ct))

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
                        if not m:
                            continue
                        print (u"Template:%s" % m.group(1)).encode('utf-8')
                    else:
                        pat = fn_pat
                        m = pat.match(src)
                        if not m:
                            continue
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
        log.info("Wiping all Kuma documents and revisions")
        kc = self.kumadb.cursor()
        kc.execute("""
            SET FOREIGN_KEY_CHECKS = 0;
            TRUNCATE wiki_taggeddocument;
            TRUNCATE wiki_documenttag;
            TRUNCATE wiki_revision;
            TRUNCATE wiki_document;
        """)

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
        ns_list = '(%s)' % (', '.join(str(x) for x in MT_MIGRATED_NS_IDS))

        # TODO: Migrate pages from namespaces other than 0

        if self.options['all']:
            # Migrating all pages trumps any other criteria
            where = """
                WHERE page_namespace IN %s
                ORDER BY page_timestamp DESC
            """ % (ns_list)
            self.cur.execute("SELECT count(*) FROM pages %s" % where)
            log.info("Gathering ALL %s pages..." %
                     self.cur.fetchone()[0])
            iters.append(self._query("SELECT * FROM pages %s" % where))

        elif self.options['slug']:
            # Use the slug in namespace 0, or parse apart slug and namespace ID
            # if a colon is present.
            ns, slug = 0, self.options['slug']
            if ':' in slug:
                ns_name, slug = slug.split(':', 1)
                ns = MT_NS_NAME_TO_ID.get('%s:' % ns_name, 0)

            # Migrating a single page...
            log.info("Searching for %s" % self.options['slug'])
            iters.append(self._query("""
                SELECT *
                FROM pages
                WHERE
                    page_namespace = %s AND
                    page_title = %s
                ORDER BY page_timestamp DESC
            """, ns, slug))

        else:
            # TODO: Refactor these copypasta queries into something DRYer?

            if self.options['most_viewed'] > 0:
                # Grab the most viewed pages
                log.info("Gathering %s most viewed pages..." %
                         self.options['most_viewed'])
                iters.append(self._query("""
                    SELECT p.*, pc.*
                    FROM pages AS p, page_viewcount AS pc
                    WHERE
                        pc.page_id=p.page_id AND
                        page_namespace IN %s
                    ORDER BY pc.page_counter DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['most_viewed']))

            if self.options['recent'] > 0:
                # Grab the most recently modified
                log.info("Gathering %s recently modified pages..." %
                         self.options['recent'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace IN %s
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['recent']))

            if self.options['longest'] > 0:
                # Grab the longest pages
                log.info("Gathering %s longest pages..." %
                         self.options['longest'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace IN %s
                    ORDER BY length(page_text) DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['longest']))

            if self.options['redirects'] > 0:
                # Grab the redirect pages
                log.info("Gathering %s redirects from MindTouch..." %
                         self.options['redirects'])
                # HACK: Need to use "%%%%" here, just to get one "%". It's
                # stinky, but it's because this string goes twice through %
                # formatting - once for page namespace list, and once for SQL
                # escaping in Django.
                iters.append(self._query("""
                    SELECT * FROM pages
                    WHERE
                        page_namespace IN %s AND
                        page_text LIKE '#REDIRECT%%%%'
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['redirects']))

            if self.options['nonen'] > 0:
                # Grab non-en pages. Might catch a few pages with "en/" in the
                # title, but not in the page_language.
                log.info("Gathering %s pages in locales other than en-US..." %
                         self.options['nonen'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace IN %s AND
                          page_language <> 'en'
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['nonen']))

        return itertools.chain(*iters)

    @transaction.commit_on_success
    def update_document(self, r):
        """Update Kuma document from given MindTouch page record"""
        # Build the page slug from namespace + title or display name
        locale, slug = self.get_kuma_locale_and_slug_for_page(r)

        # Skip this document, if it has a blank timestamp.
        # The only pages in production that have no timestamp are either in the
        # Special: namespace (not migrated), or a couple of untitled and empty
        # pages under the Template: or User: namespaces.
        if not r['page_timestamp']:
            log.debug("\t%s / %s (%s) skipped, no timestamp" %
                      (locale, slug, r['page_display_name']))
            return False

        # Check to see if this doc has already been migrated, and if the
        # exising is doc is up to date.
        page_ts = self.parse_timestamp(r['page_timestamp'])
        last_mod = self.docs_migrated.get(r['page_id'], (None, None))[1]
        if (not self.options['update_documents'] and last_mod is not None
                and last_mod >= page_ts):
            log.debug("\t%s / %s (%s) up to date" %
                      (locale, slug, r['page_display_name']))
            return False

        # Check to see if this doc's content hash falls in the list of User:
        # namespace content we want to exclude.
        if r['page_namespace'] == MT_NS_NAME_TO_ID['User:']:
            content_hash = (hashlib.md5(r['page_text'].encode('utf-8'))
                                   .hexdigest())
            if content_hash in USER_NS_EXCLUDED_CONTENT_HASHES:
                log.debug("\t%s / %s (%s) matched User: content exclusion list" %
                          (locale, slug, r['page_display_name']))
                return False

        # Check to see if this page's content is too long, skip if so.
        if len(r['page_text']) > self.options['maxlength']:
            log.debug("\t%s / %s (%s) skipped, page too long (%s > %s max)" %
                      (locale, slug, r['page_display_name'],
                       len(r['page_text']), self.options['maxlength']))
            return False

        log.info("\t%s / %s (%s)" % (locale, slug, r['page_display_name']))

        # Ensure that the document exists, and has the MindTouch page ID
        doc, created = Document.objects.get_or_create(
            locale=locale, slug=slug,
            title=r['page_display_name'], defaults=dict(
                category=CATEGORIES[0][0],
            ))
        doc.mindtouch_page_id = r['page_id']

        if created:
            log.info("\t\tNew document created. (ID=%s)" % doc.pk)
        else:
            log.info("\t\tDocument already exists. (ID=%s)" % doc.pk)

        tags = self.get_tags_for_page(r)

        self.update_past_revisions(r, doc, tags)
        self.update_current_revision(r, doc, tags)

        return True

    def update_past_revisions(self, r_page, doc, tags):
        """Update past revisions for the given page row and document"""
        ct_saved, ct_skipped, ct_error = 0, 0, 0

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
                    ct_skipped += 1
                    continue

            # Check to see if this revision's content is too long, skip if so.
            if len(r['old_text']) > self.options['maxlength']:
                ct_skipped += 1
                continue

            # Build up a dict of the row for the revision
            ts = self.parse_timestamp(r['old_timestamp'])
            rev_data = dict(
                document_id=doc.pk,
                mindtouch_old_id=r['old_id'],
                is_mindtouch_migration=1,
                slug=doc.slug,
                title=doc.title,
                tags=tags,
                is_approved=True,
                significance=SIGNIFICANCES[0][0],
                summary='',
                keywords='',
                content=self.convert_page_text(r['old_text']),
                comment=r['old_comment'],
                created=ts,
                creator_id=self.get_django_user_id_for_deki_id(r['old_user']),
                reviewed=ts,
                reviewer_id=self.get_superuser_id()
            )
            revs.append(rev_data)

            ct_saved += 1

        if len(revs):

            # Build REPLACE INTO style SQL placeholders for the revisions. eg.:
            # (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s),
            # (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s),
            # (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            col_names = revs[0].keys()
            one_row = '(%s)' % ', '.join('%s' for x in col_names)
            placeholders = ",\n".join(one_row for x in revs)

            # Flatten list of revisions data in chronological order, so that we
            # get roughly time-sequential IDs and a flat list to fill the
            # placeholders.
            revs_flat = [rev[name]
                         for rev in sorted(revs, key=lambda x: x['created']) 
                         for name in col_names]

            # Build and execute a giant query to save all the revisions.
            sql = ("REPLACE INTO wiki_revision (%s) VALUES %s" %
                   (', '.join(col_names), placeholders))
            kc.execute(sql, revs_flat)

        self.rev_ct += ct_saved + ct_skipped + ct_error
        log.info("\t\tPast revisions: %s saved, %s skipped, %s errors" %
                 (ct_saved, ct_skipped, ct_error))

    def update_current_revision(self, r, doc, tags):
        """Update the current revision associated with a doc and MT page row"""
        # HACK: Using old_id of None to indicate current MindTouch revision.
        # All revisions of a Kuma document have revision records, whereas
        # MindTouch only tracks "old" revisions.
        p_id = r['page_user_id']
        rev, created = Revision.objects.get_or_create(document=doc,
            is_mindtouch_migration=True, mindtouch_old_id=None, defaults=dict(
                creator_id=self.get_django_user_id_for_deki_id(p_id),
                is_approved=True,
                significance=SIGNIFICANCES[0][0],))

        # Check to see if the current revision is up to date, in which case we
        # can skip the update and save a little time.
        page_ts = self.parse_timestamp(r['page_timestamp'])
        if (not self.options['update_documents'] and not created and
                page_ts <= rev.created):
            log.info("\t\tCurrent revision up to date. (ID=%s)" % rev.pk)
            return

        rev.created = rev.reviewed = page_ts
        rev.slug = doc.slug
        rev.title = doc.title
        rev.tags = tags
        rev.content = self.convert_page_text(r['page_text'])

        # HACK: Some comments end up being too long, but just truncate.
        rev.comment = r['page_comment'][:255]

        # Save, and force to current revision.
        rev.save()
        rev.make_current()

        if created:
            log.info("\t\tCurrent revision created. (ID=%s)" % rev.pk)
        else:
            log.info("\t\tCurrent revision updated. (ID=%s)" % rev.pk)

    def convert_page_text(self, pt):
        """Given a page row from MindTouch, do whatever needs doing to convert
        the page content for Kuma."""

        if pt.startswith('#REDIRECT'):
            pt = self.convert_redirect(pt)

        pt = self.convert_code_blocks(pt)
        # TODO: bug 710728 - Convert and normalize template calls
        # TODO: bug 710726 - Convert intra-wiki links?

        return pt

    def convert_redirect(self, pt):
        """Convert MindTouch-style page redirects to Kuma-style"""
        m = MT_REDIR_PAT.match(pt)
        if m:
            # TODO: Do we need a convert_title function for locale parsing (eg.
            # as part of bug 710724?)
            title = m.group(1)
            href = reverse('wiki.document', args=[title])
            pt = REDIRECT_CONTENT % dict(href=href, title=title)
        return pt

    def convert_code_blocks(self, pt):
        soup = BeautifulSoup(pt)
        for code_block in soup.findAll('pre',
                                       {"class": "deki-transform",
                                        "function": "syntax.JavaScript",
                                       }):
            code_block['class'] = "brush: js"
            del code_block['function']
        return str(soup)

    def get_tags_for_page(self, r):
        """For a given page row, get the list of tags from MindTouch and build
        a string representation for Kuma revisions."""
        wc = self.wikidb.cursor()
        wc.execute("""
            SELECT t.tag_name
            FROM tag_map AS tm, tags AS t, pages AS p
            WHERE
                t.tag_id=tm.tagmap_tag_id AND
                p.page_id=tm.tagmap_page_id AND
                p.page_id=%s
        """, (r['page_id'],))

        # HACK: To prevent MySQL truncation warnings, constrain the imported
        # tags to 100 chars. Who wants tags that long, anyway?
        mt_tags = [row[0][:100] for row in wc]

        # To build a string representation, we need to quote or not quote based
        # on the presence of commas or spaces in the tag name.
        quoted = []
        if len(mt_tags):
            for tag in mt_tags:
                if u',' in tag or u' ' in tag:
                    quoted.append('"%s"' % tag)
                else:
                    quoted.append(tag)

        return u', '.join(quoted)

    def get_kuma_locale_and_slug_for_page(self, r):
        """Given a MindTouch page row, derive the Kuma locale and slug."""

        # Come up with a complete slug, along with MT namespace mapped to name.
        ns_name = MT_NS_ID_TO_NAME.get(r['page_namespace'], '')
        slug = '%s%s' % (ns_name, r['page_title'] or r['page_display_name'])

        # Start from the default language
        mt_language = ''

        # If the page is not in a namespace, and it has paths in the slug...
        if ns_name == '' and '/' in slug:
            # Treat the first part of the slug path as locale and snip it off.
            mt_language, new_slug = slug.split('/', 1)
            if mt_language in MT_TO_KUMA_LOCALE_MAP:
                # If it's a known language, then use the new slug
                slug = new_slug
            else:
                # Otherwise, we'll preserve the slug and tack the default
                # locale onto it. (eg. ServerJS/FAQ, CommonJS/FAQ)
                mt_language = ''
        
        if mt_language == '':
            # Finally, fall back to the explicit page language
            mt_language = r['page_language']

        # Map from MT language to Kuma locale.
        locale = MT_TO_KUMA_LOCALE_MAP.get(mt_language.lower(), '')

        return (locale, slug)

    def get_django_user_id_for_deki_id(self, deki_user_id):
        """Given a Deki user ID, come up with a Django user object whether we
        need to migrate it first or just fetch it."""
        # If we don't already have this Deki user cached, look up or migrate
        if deki_user_id not in self.user_ids:

            # Look up the user straight from the database
            self.cur.execute("SELECT * FROM users AS u WHERE u.user_id = %s",
                             (deki_user_id,))
            r = list(self._query_dicts(self.cur))

            if not len(r):
                # HACK: If, for some reason the user is missing from MindTouch,
                # just put and use the superuser. Seems to happen mainly for
                # user #0, which is probably superuser anyway.
                return self.get_superuser_id()

            # Build a DekiUser object from the database record, and make sure
            # it's active.
            user = r[0]
            deki_user = DekiUser(id=user['user_id'],
                                 username=user['user_name'],
                                 fullname=user['user_real_name'],
                                 email=user['user_email'],
                                 gravatar='',)
            deki_user.is_active = True

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
            user = DekiUserBackend.get_or_create_user(deki_user,
                                                      sync_attrs=[])
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
