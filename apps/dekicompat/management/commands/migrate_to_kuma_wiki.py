# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

"""
Migration tool that copies pages from a MindTouch database to the Kuma wiki.

Should be idempotent - ie. running this repeatedly should result only in
updates, and not duplicate documents or repeated revisions.

TODO
* https://bugzilla.mozilla.org/show_bug.cgi?id=710713
* https://bugzilla.mozilla.org/showdependencytree.cgi?id=710713&hide_resolved=1
"""
import datetime
import hashlib
import itertools
import json
import os
import re
import sys
import time
from optparse import make_option

# HACK: This is the fattest hack I've written in awhile. I blame ianbicking
# http://blog.ianbicking.org/illusive-setdefaultencoding.html
reload(sys)
sys.setdefaultencoding('utf8')

from BeautifulSoup import BeautifulSoup
from pyquery import PyQuery as pq

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import MultipleObjectsReturned
from django.core.management.base import (BaseCommand, NoArgsCommand,
                                         CommandError)
from django.core.files.base import ContentFile
import django.db
from django.db import connections, transaction
from django.db.utils import DatabaseError
from django.template.defaultfilters import slugify
from django.utils import encoding, hashcompat
from django.db.models import F

import commonware.log

from sumo.urlresolvers import reverse

from wiki.models import (Document, Revision, CATEGORIES, SIGNIFICANCES,
                         Attachment, AttachmentRevision)

from wiki.models import REDIRECT_CONTENT
import wiki.content
from wiki.content import (ContentSectionTool, CodeSyntaxFilter,
                          DekiscriptMacroFilter)

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
MT_MIGRATED_NS_IDS = [MT_NS_NAME_TO_ID[x] for x in (
    '', 'Talk:', 'User:', 'User_talk:', 'Project:', 'Project_talk:',
    'Template:', 'Template_talk:',
)]

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
        make_option('--withsyntax', dest="withsyntax", type="int", default=0,
                    help="Migrate # of documents with syntax blocks"),
        make_option('--withscripts', dest="withscripts", type="int", default=0,
                    help="Migrate # of documents that use scripts"),
        make_option('--withtemplates', dest="withtemplates", type="int",
                    default=0, help="Migrate # of template documents"),
        make_option('--withlanguages', dest="withlanguages", type="int",
                    default=0,
                    help="Migrate # of English documents with other "
                    "languages"),
        make_option('--withemptycontent', action="store_true",
                    dest="withemptycontent", default=False,
                    help="Migrate all documents with empty current revision "
                         "content."),
        make_option('--withunreviewed', action="store_true",
                    dest="withunreviewed", default=False,
                    help="Migrate all documents with unreviewed current "
                         "revision."),

        make_option('--fromlist', type="string", default='',
                    help="Migrate pages from a list in the named file."),

        make_option('--files', action="store_true", dest="files", default=False,
                    help="Migrate all files."),

        make_option('--syntax-metrics', action="store_true",
                    dest="syntax_metrics", default=False,
                    help="Measure syntax highlighter usage, skip migration"),
        make_option('--skip-translations', action="store_true",
                    dest="skip_translations", default=False,
                    help="Skip migrating translated children of documents"),
        make_option('--skip-breadcrumbs', action="store_true",
                    dest="skip_breadcrumbs", default=False,
                    help="Skip migrating breadcrumb parents of documents"),

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
        elif options['syntax_metrics']:
            self.handle_syntax_metrics(rows)
        else:
            self.handle_migration(rows)
            if not options['skip_translations']:
                rows = self.gather_pages()
                self.make_languages_relationships(rows)
                self.cleanup_circular_translations()
            if not options['skip_breadcrumbs']:
                rows = self.gather_pages()
                self.make_breadcrumb_relationships(rows)
        if options['files']:
            self.handle_file_migration()

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
        self.missing_files = []

    def handle_migration(self, rows):
        self.docs_migrated = self.index_migrated_docs()
        log.info(u"Found %s docs already migrated" %
                 len(self.docs_migrated.values()))

        start_ts = ts_now = ts_last_status = time.time()

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
                    log.info(u"Reached limit of %s documents migrated" %
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
                    log.error(u'\t\tPROBLEM %s' % type(e))
                    error_ct += 1

            ts_now = time.time()
            duration = ts_now - start_ts
            total_ct = ct + skip_ct + error_ct
            # Emit status every 5 seconds
            if ((ts_now - ts_last_status) > 5.0):
                ts_last_status = time.time()
                log.info(u"Rate: %s docs/sec, %s secs/doc, "
                         "%s total in %s seconds" %
                         ((total_ct + 1) / (duration + 1),
                          (duration + 1) / (total_ct + 1),
                          total_ct, duration))
                log.info(u"Rate: %s revs/sec, %s total in %s seconds" %
                         ((self.rev_ct + 1) / (duration + 1),
                          self.rev_ct, duration))

        log.info(u"Migration finished: %s seconds, %s migrated, "
                 u"%s skipped, %s errors" %
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

    def handle_syntax_metrics(self, rows):
        """Discover the languages used in syntax highlighting"""
        for r in rows:
            pt = r['page_text']
            soup = BeautifulSoup(pt)
            blocks = soup.findAll()
            for block in blocks:
                for attr in block.attrs:
                    if attr[0] == 'function':
                        print (u"%s\t%s\t%s" % (r['page_title'], block.name,
                                                    attr[1])).encode('utf-8')

    def _get_mindtouch_pages_row(self, page_id):
        sql = """
            SELECT *
            FROM pages
            WHERE page_id = %d
        """ % page_id
        try:
            rows = self._query(sql)
        except Exception, e:
            log.error(u"\tpage_id %s error %s" %
                      (page_id, e))
        single_row = None
        for row in rows:
            single_row = row
        return single_row

    def _migrate_necessary_mindtouch_pages(self, migrate_ids):
        """ Given a list of mindtouch ids, migrate only the necessary pages."""
        existing = [str(x['mindtouch_page_id']) for x in
                    Document.objects.filter(mindtouch_page_id__in=migrate_ids)
                                    .values('mindtouch_page_id')]
        need_migrate_ids = [str(x) for x in migrate_ids
                            if str(x) not in existing]
        if need_migrate_ids:
            sql = "SELECT * FROM pages WHERE page_id in (%s)" % (
                ",".join(need_migrate_ids))
            rows = self._query(sql)
            self.handle_migration(rows)

    def _add_parent_ids(self, r, bc_ids):
        """ Recursively add parent ids to breadcrumb ids list. """
        parent_row = self._get_mindtouch_pages_row(r['page_parent'])
        if parent_row:
            bc_ids.insert(0, r['page_parent'])
            self._add_parent_ids(parent_row, bc_ids)
        return bc_ids

    @transaction.commit_on_success(using='default')
    def make_breadcrumb_relationships(self, rows):
        """Set the topic_parent for Kuma pages using parent_id"""
        log.info(u"Building parent/child breadcrumb tree...")
        seen_docs = set()
        for r in rows:
            if not r['page_text'].strip():
                # Skip blank pages.
                continue
            if not r['page_parent']:
                # If there's no parent here, skip along.
                continue
            bc_ids = self._add_parent_ids(r, [r['page_id']])
            if not self.options['all']:
                # Don't bother migrating as needed, if --all was already done.
                log.info(u"Migrating breadcrumb ids: %s" % bc_ids)
                self._migrate_necessary_mindtouch_pages(bc_ids)
            parent_id = bc_ids.pop(0)
            try:
                parent_doc = Document.objects.get(mindtouch_page_id=parent_id)
                for id in bc_ids:
                    try:
                        doc = Document.objects.get(mindtouch_page_id=id)
                        if not id in seen_docs:
                            # Only bother updating this document if we haven't done
                            # so already in this run.
                            log.info(u"\t%s -> %s" % (parent_doc, doc))
                            doc.parent_topic = parent_doc
                            doc.save()
                        seen_docs.add(id)
                        parent_doc = doc
                    except Document.DoesNotExist:
                        # If a parent doc in the chain does not exist, just
                        # ignore its absence and snip it out of the path.
                        log.error(u"\t\t%s not found in chain" % id)
            except Document.DoesNotExist:
                # Some pages are skipped by migration, regardless of whether
                # another page calls it parent. Most of these cases look like
                # boilerplate User:* pages
                log.error(u"\t\t%s not found in chain" % parent_id)

    @transaction.commit_manually(using='default')
    def make_languages_relationships(self, rows):
        """Set the parent_id of Kuma pages using wiki.languages params"""
        log.info(u"Building parent/child locale tree...")
        wl_pat = re.compile(r"""^wiki.languages\((.+)\)""")
        # language_tree is {page_id: [child_id, child_id, ...], ...}
        language_tree = {}
        for r in rows:
            if not r['page_text'].strip():
                # Page empty, so skip it.
                continue
            if not r['page_title'].lower().startswith('en/'):
                # Page is not an english page, skip it
                continue
            # Build the page slug from namespace + title or display name
            locale, slug = self.get_kuma_locale_and_slug_for_page(r)
            parent_id = r['page_id']
            doc = pq(r['page_text'])
            spans = doc.find('span.script')
            for span in spans:
                src = unicode(span.text).strip()
                if src.startswith('wiki.languages'):
                    m = wl_pat.match(src)
                    if not m:
                        continue
                    language_tree[parent_id] = []
                    page_languages_json = m.group(1).strip()
                    page_languages = {}
                    try:
                        page_languages = json.loads(page_languages_json)
                    except ValueError:
                        log.error(u"\t%s/%s (%s) error parsing wiki.languages JSON" %
                                  (locale, slug, r['page_display_name']))
                        continue
                    vals = page_languages.values()
                    if not vals:
                        continue
                    wc = self.wikidb.cursor()
                    sql = """
                        SELECT page_id
                        FROM pages
                        WHERE page_title IN ('%s')
                        AND page_namespace = 0
                    """ % "','".join(vals)
                    try:
                        wc.execute(sql)
                    except Exception, e:
                        log.error(u"\t%s/%s (%s) error %s" %
                                  (locale, slug, r['page_display_name'], e))
                        continue
                    for row in wc:
                        language_tree[parent_id].append(row[0])

        log.info(u"Building translation relationships...")
        kc = self.kumadb.cursor()
        for parent_id, children in language_tree.items():
            # Now that we have our tree of docs and children, migrate them
            # as necessary
            try:
                parent_doc = Document.objects.get(mindtouch_page_id=parent_id)
            except Document.DoesNotExist:
                rows = self._query("SELECT * FROM pages WHERE page_id = %s" %
                                   parent_id)
                self.handle_migration(rows)
                try:
                    parent_doc = Document.objects.get(mindtouch_page_id=parent_id)
                except Document.DoesNotExist:
                    # Ugh, even after migration we didn't end up with the
                    # parent doc
                    continue

            # Migrate any child documents that haven't already been
            self._migrate_necessary_mindtouch_pages(children)

            # All parents and children migrated, now set parent_id
            # TODO: refactor this to source_id when we change to
            # source/translation relationship model
            child_ids = [str(x) for x in children]
            if child_ids:
                log.info(u"\t%s (%s)" % (parent_doc.full_path, parent_doc.title))
                sql = """
                    UPDATE wiki_document
                    SET parent_id = %s
                    WHERE mindtouch_page_id IN (%s)
                """ % (parent_doc.id, ",".join(child_ids))
                kc.execute(sql)
                log.info(u"\t\tUpdated %s documents with parent ID." % kc.rowcount)
                transaction.commit()

    def cleanup_circular_translations(self):
        """In past migrations, some objects ended up pointing at themselves as
        translation parents. Fix that."""
        log.info(u"Cleaning up circular translations...")
        for doc in Document.objects.filter(parent=F('id')):
            log.info(u"\t%s" % doc)
            doc.parent = None
            doc.save()
    
    @transaction.commit_on_success
    def wipe_documents(self):
        """Delete all documents"""
        log.info(u"Wiping all Kuma documents and revisions")
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
            log.info(u"Gathering ALL %s pages..." %
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
            log.info(u"Searching for %s" % self.options['slug'])
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
                log.info(u"Gathering %s most viewed pages..." %
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
                log.info(u"Gathering %s recently modified pages..." %
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
                log.info(u"Gathering %s longest pages..." %
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
                log.info(u"Gathering %s redirects from MindTouch..." %
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
                log.info(u"Gathering %s pages in locales other than en-US..." %
                         self.options['nonen'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace IN %s AND
                          page_language <> 'en'
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['nonen']))

            if self.options['withsyntax'] > 0:
                log.info(u"Gathering %s pages with syntax highlighting" %
                         self.options['withsyntax'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace IN %s AND
                          page_text like '%%%%function="syntax.%%%%'
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['withsyntax']))

            if self.options['withscripts'] > 0:
                log.info(u"Gathering %s pages that use scripts" %
                         self.options['withscripts'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace IN %s AND
                          page_text like '%%%%span class="script"%%%%'
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """ % (ns_list, '%s'), self.options['withscripts']))

            if self.options['withtemplates'] > 0:
                log.info(u"Gathering %s templates" %
                         self.options['withtemplates'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_namespace=%s
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """, MT_NS_NAME_TO_ID['Template:'],
                     self.options['withtemplates']))

            if self.options['withlanguages'] > 0:
                log.info(u"Gathering %s English pages that have languages" %
                         self.options['withlanguages'])
                iters.append(self._query("""
                    SELECT *
                    FROM pages
                    WHERE page_text like '%%%%wiki.languages%%%%' AND
                          LOWER(page_title) like 'en/%%%%'
                    ORDER BY page_timestamp DESC
                    LIMIT %s
                """, self.options['withlanguages']))

            if self.options['withemptycontent']:
                log.info(u"Gathering ALL pages corresponding to documents whose "
                         "current revision has empty content")
                sql = """
                    SELECT d.mindtouch_page_id
                    FROM wiki_document AS d, wiki_revision AS r
                    WHERE
                        r.id = d.current_revision_id AND
                        r.is_mindtouch_migration=1 AND
                        r.content = ''
                        GROUP BY d.id
                """
                # Can't easily join between DBs, so this is painful:
                kc = self.kumadb.cursor()
                kc.execute(sql)
                for row in kc:
                    iters.append(self._query("""
                        SELECT * FROM pages
                        WHERE page_id = %s
                    """, row[0]))

            if self.options['withunreviewed']:
                log.info(u"Gathering ALL pages corresponding to documents whose "
                         "current revision is unreviewed")
                sql = """
                    SELECT d.mindtouch_page_id
                    FROM wiki_document AS d, wiki_revision AS r
                    WHERE
                        r.id = d.current_revision_id AND
                        r.is_mindtouch_migration=1 AND
                        r.reviewed IS NULL
                        GROUP BY d.id
                """
                # Can't easily join between DBs, so this is painful:
                kc = self.kumadb.cursor()
                kc.execute(sql)
                for row in kc:
                    iters.append(self._query("""
                        SELECT * FROM pages
                        WHERE page_id = %s
                    """, row[0]))

            if self.options['fromlist']:
                # Read in the page title list, carefully snipping off the \n's
                names = [x[:-1] for x in open(self.options['fromlist'])]
                log.info(u"Gathering %s pages from %s" %
                         (len(names), self.options['fromlist']))

                # Paginate the page title list so we can do chunked queries. I
                # think queries can be pretty large, but not arbitrarily so.
                page_len = 500
                pages = [names[x:x+page_len]
                         for x in range(0, len(names), page_len)]
                
                # Perform the chunked queries, collect the iterators.
                page_num = 0
                for page in pages:
                    page_num += 1
                    log.debug("\tpage %s of %s (%s titles)" %
                              (page_num, len(pages), len(page)))
                    sql = """
                        SELECT * FROM pages
                        WHERE page_title IN (%s)
                    """ % ','.join(['%s' for x in range(0, len(page))])
                    iters.append(self._query(sql, *page))

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
            log.debug(u"\t%s/%s (%s) skipped, no timestamp" %
                      (locale, slug, r['page_display_name']))
            return False

        # Check to see if this doc has already been migrated, and if the
        # exising is doc is up to date.
        page_ts = self.parse_timestamp(r['page_timestamp'])
        last_mod = self.docs_migrated.get(r['page_id'], (None, None))[1]
        if (not self.options['update_documents'] and last_mod is not None
                and last_mod >= page_ts):
            # log.debug(u"\t%s/%s (%s) up to date" %
            #           (locale, slug, r['page_display_name']))
            return False

        # Check to see if this doc's content hash falls in the list of User:
        # namespace content we want to exclude.
        if r['page_namespace'] == MT_NS_NAME_TO_ID['User:']:
            content_hash = (hashlib.md5(r['page_text'].encode('utf-8'))
                                   .hexdigest())
            if content_hash in USER_NS_EXCLUDED_CONTENT_HASHES:
                # log.debug(u"\t%s/%s (%s) matched User: content exclusion list" %
                #           (locale, slug, r['page_display_name']))
                return False

        # Skip migrating Template:MindTouch/* templates
        if slug.startswith('Template:MindTouch'):
            log.debug(u"\t%s/%s (%s) skipped, was a MindTouch default template" %
                      (locale, slug, r['page_display_name']))
            return False

        # Check to see if this page's content is too long, skip if so.
        if len(r['page_text']) > self.options['maxlength']:
            log.debug(u"\t%s/%s (%s) skipped, page too long (%s > %s max)" %
                      (locale, slug, r['page_display_name'],
                       len(r['page_text']), self.options['maxlength']))
            return False

        log.info(u"\t%s/%s (%s)" % (locale, slug, r['page_display_name']))

        try:
            # Try to get just a single document for the page ID.
            doc = Document.objects.get(mindtouch_page_id=r['page_id'])
            created = False
        except MultipleObjectsReturned:
            # If there are multiples, then just get the first.
            doc = Document.objects.filter(mindtouch_page_id=r['page_id'])[0]
            created = False
        except Document.DoesNotExist:
            # Otherwise, try to create a new one.
            doc, created = Document.objects.get_or_create(
                locale=locale, slug=slug,
                defaults=dict(
                    category=CATEGORIES[0][0]
                ))
            doc.mindtouch_page_id = r['page_id']

        # Ensure the title is up to date.
        doc.title = r['page_display_name']
        doc.save()

        if created:
            log.info(u"\t\tNew document created. (ID=%s)" % doc.pk)
        else:
            log.info(u"\t\tDocument already exists. (ID=%s)" % doc.pk)

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
                content=self.convert_page_text(r_page, r['old_text']),
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
        log.info(u"\t\tPast revisions: %s saved, %s skipped, %s errors" %
                 (ct_saved, ct_skipped, ct_error))

    def update_current_revision(self, r, doc, tags):
        """Update the current revision associated with a doc and MT page row"""
        # HACK: Using old_id of None to indicate current MindTouch revision.
        # All revisions of a Kuma document have revision records, whereas
        # MindTouch only tracks "old" revisions.
        p_id = r['page_user_id']

        # Check to see if the current revision is up to date, in which case we
        # can skip the update and save a little time.
        page_ts = self.parse_timestamp(r['page_timestamp'])
        if (doc.current_revision and
                (not self.options['update_documents'] and
                 page_ts <= doc.current_revision.created)):
            log.info(u"\t\tCurrent revision up to date.")
            return

        # Always create a new current revision; never overwrite or modify the
        # existing one, even if we're just technically updating.
        rev = Revision(document=doc, 
                       slug=doc.slug, title=doc.title, tags=tags,
                       created=page_ts, reviewed=page_ts,
                       # Process the revision content along the way...
                       content=self.convert_page_text(r, r['page_text']),
                       # HACK: Some rare comments end up being too long, but
                       # just truncate.
                       comment = r['page_comment'][:255],
                       # This is a mindtouch migration, but the current rev in
                       # MT has no old_id.
                       is_mindtouch_migration=True, mindtouch_old_id=None,
                       creator_id=self.get_django_user_id_for_deki_id(p_id),
                       is_approved=True,
                       significance=SIGNIFICANCES[0][0],)

        # Save, and force to current revision.
        rev.save()
        rev.make_current()

        # If this is a template, set it as in need of template review
        if doc.slug.startswith('Template:'):
            rev.review_tags.set('template') 

        log.info(u"\t\tNew current revision created. (ID=%s)" % rev.pk)

    def convert_page_text(self, r, pt):
        """Given a page row from MindTouch, do whatever needs doing to convert
        the page content for Kuma."""

        # If this is a redirect, just convert the redirect.
        if pt.startswith('#REDIRECT'):
            return self.convert_redirect(pt)

        # If this is a template, just do template conversion
        ns_name = MT_NS_ID_TO_NAME.get(r['page_namespace'], '')
        if ns_name == 'Template:':
            return self.convert_dekiscript_template(pt)

        # Otherwise, run through the rest of the conversions.
        pt = self.convert_code_blocks(pt)
        pt = self.convert_dekiscript_calls(pt)
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
        pt = ContentSectionTool(pt).filter(CodeSyntaxFilter).serialize()
        return pt

    def convert_dekiscript_calls(self, pt):
        return (wiki.content.parse(pt).filter(DekiscriptMacroFilter)
                    .serialize())

    def convert_dekiscript_template(self, pt):
        """Do what we can to convert DekiScript templates into EJS templates.

        This is an incomplete process, but it tries to take care off as much as
        it can so that human intervention is minimized."""

        # Many templates start with this prefix, which corresponds to <% in EJS
        pre = '<pre class="script">'
        if pt.startswith(pre):
            pt = "<%%\n%s" % pt[len(pre):]

        # Many templates end with this postfix, which corresponds to %> in EJS
        post = '</pre>'
        if pt.endswith(post):
            pt = "%s\n%%>" % pt[:0-len(post)]

        # Template source is usually HTML encoded inside the <pre>
        pt = (pt.replace('&amp;', '&')
                .replace('&lt;', '<')
                .replace('&gt;', '>')
                .replace('&quot;', '"'))

        # String concatenation is '..' in DS, '+' in EJS
        pt = pt.replace('..', '+')

        # ?? in DS is pretty much || in EJS
        pt = pt.replace('??', '||')

        # No need for DS 'let' in EJS
        pt = pt.replace('let ', '')

        # This is a common sequence at the start of many templates. It clobbers
        # the url API, and needs correcting.
        pt = (pt.replace('var uri =', 'var u =')
                .replace('uri.path[', 'u.path['))

        return pt

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
        title = r['page_title'] or r['page_display_name']
        slug = '%s%s' % (ns_name, title)

        # Start from the default language
        mt_language = ''

        # If the page has path segments in its title...
        if '/' in title:
            # Treat the first part of the slug path as locale and snip it off.
            mt_language, new_title = title.split('/', 1)
            if mt_language.lower() in MT_TO_KUMA_LOCALE_MAP:
                # If it's a known language, then rebuild the slug
                slug = '%s%s' % (ns_name, new_title)
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

    def get_filesystem_storage_root(self):
        cursor = self.wikidb.cursor()
        cursor.execute("""
            SELECT config_value
            FROM   config
            WHERE  config_key = 'storage/fs/path';
        """)
        return cursor.fetchall()[0][0]

    def handle_file_migration(self):
        cursor = self.wikidb.cursor()
        # Get as much information about each file as possible
        # up-front; some of it's redundant with stuff we'll look up
        # later, but getting it early helps a bit with processing.
        #
        # TODO: This currently does *not* migrate files which are
        # marked as deleted in MindTouch. I'm not sure the file
        # contents for those are even retrievable, but is it worth
        # looking into?
        cursor.execute("""
            SELECT res_id, res_headrev, res_create_timestamp,
                   res_update_timestamp, res_create_user_id,
                   res_update_user_id, resrev_name, resrev_mimetype
            FROM   resources
            WHERE  res_type = 2
                   AND resrev_deleted = 0;
        """)
        file_rows = list(self._query_dicts(cursor))
        for row in file_rows:
            self.handle_file(row)
        return

    def handle_file(self, row):
        # The MindTouch ID we store is actually the public-facing API
        # file ID, not the database ID of the resource.
        cursor = self.wikidb.cursor()
        cursor.execute("""
            SELECT resource_id, file_id
            FROM resourcefilemap
            WHERE resource_id = %s
        """ % row['res_id'])
        res_row = list(self._query_dicts(cursor))[0]

        print "Start of migration for file with MindTouch ID %s" % res_row['file_id']

        attachment, created = Attachment.objects.get_or_create(
            mindtouch_attachment_id=res_row['file_id'],
            defaults={
                'title': row['resrev_name'],
                'slug': slugify(row['resrev_name']),
                'modified': row['res_update_timestamp']})

        # Now get the revisions.
        cursor = self.wikidb.cursor()
        cursor.execute("""
            SELECT resrev_id, resrev_user_id, resrev_name,
                   resrev_change_description, resrev_timestamp,
                   resrev_content_id, resrev_mimetype
            FROM   resourcerevs
            WHERE  resrev_res_id = %s
                   AND resrev_deleted = 0;
        """ % row['res_id'])
        rev_rows = list(self._query_dicts(cursor))
        for rev_row in rev_rows:
            # Make sure we haven't migrated this revision already.
            if not AttachmentRevision.objects.filter(mindtouch_old_id=rev_row['resrev_id']).exists():
                self.handle_file_revision(attachment, row, res_row, rev_row)
        revs = attachment.revisions.order_by('-created')
        if revs:
            revs[0].make_current()
        print "End of migration for file with MindTouch ID %s" % res_row['file_id']
        

    def handle_file_revision(self, attachment, row, res_row, rev_row):
        # Now we get the contents of the file, and build a Revision.
        print "Start of migration for file revision with MindTouch ID %s" % rev_row['resrev_id']
        cursor = self.wikidb.cursor()
        cursor.execute("""
            SELECT rescontent_value, rescontent_mimetype,
                   rescontent_location, rescontent_res_rev
            FROM   resourcecontents
            WHERE  rescontent_id = %s
        """ % rev_row['resrev_content_id'])
        content_row = list(self._query_dicts(cursor))[0]

        # Now the fun part -- figuring out where to get the file
        # contents!
        #
        # We start by looking at rescontent_location; if it's not
        # NULL, it's the filesystem path of the file.
        file_contents = None
        file_path = None
        if 'rescontent_location' in rev_row and rev_row['rescontent_location'] is not None:
            file_path = rev_row['rescontent_location']
            print "Found file path in database: %s" % file_path
        # If it wasn't there, it may be in a blob in the database.
        elif 'rescontent_value' in rev_row and rev_row['rescontent_value'] is not None:
            file_contents = rev_row['rescontent_value']
            print "Found file contents in database"
        # And if it wasn't there, we get to construct a filesystem
        # path that hopefully corresponds to where the file exists!
        else:
            print "Searching filesystem for file location and contents"
            fs_root = self.get_filesystem_storage_root()
            if row['res_id'] < 1000: # MindTouch stores files with 1- 2- or 3-digit IDs differently from all others.
                file_path = os.path.join(fs_root,
                                         "%s.res" % row['res_id'],
                                         "%s.bin" % content_row['rescontent_res_rev'])
            else:
                padded_id = "%04i" % row['res_id']
                dir_id = padded_id[:3]
                file_id = padded_id[3]
                file_path = os.path.join(fs_root, dir_id,
                                         "%s.res" % file_id,
                                         "%s.bin" % content_row['rescontent_res_rev'])
            if not os.path.exists(file_path):
                print "File error (Attachment %s): cannot locate %s on filesystem, contents not in database" % (row['res_id'], file_path)
                print "Missing file's MindTouch URL would be https://developer.mozilla.org/@api/deki/files/%s/%s" % (res_row['file_id'], rev_row['resrev_name'])
                return
            else:
                print "Found file (Attachment %s): file path %s" % (row['res_id'], file_path)
        if file_path is not None:
            file_contents = open(file_path, 'rb').read()
        # Now we create an AttachmentRevision and stick the file in
        # it.
        rev = AttachmentRevision(attachment=attachment,
                                 mime_type=content_row['rescontent_mimetype'],
                                 title=rev_row['resrev_name'],
                                 slug=slugify(rev_row['resrev_name']),
                                 description='',
                                 created=rev_row['resrev_timestamp'],
                                 is_approved=True,
                                 is_mindtouch_migration=True,
                                 mindtouch_old_id=rev_row['resrev_id'])
        rev.creator_id = self.get_django_user_id_for_deki_id(rev_row['resrev_user_id'])
        rev.file.save(rev_row['resrev_name'], ContentFile(file_contents))
        rev.save()
        print "Created kuma AttachmentRevision %s for MindTouch file revision %s" % (rev.id, rev_row['resrev_id'])
        return
