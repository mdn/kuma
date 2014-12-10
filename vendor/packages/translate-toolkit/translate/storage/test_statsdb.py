#!/usr/bin/env python
from translate import storage

import os
import os.path

import py.test

from translate.storage import statsdb, factory
from translate.misc import wStringIO
from translate.filters import checks
import warnings

fr_terminology_extract = r"""
msgid ""
msgstr ""
"Project-Id-Version: GnomeGlossary\n"
"POT-Creation-Date: 2002-05-22 23:40+0200\n"
"PO-Revision-Date: 2002-05-22 23:38+0200\n"
"Last-Translator: Christophe Merlet (RedFox) <christophe@merlet.net>\n"
"Language-Team: GNOME French Team <gnomefr@traduc.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=ISO-8859-1\n"
"Content-Transfer-Encoding: 8bit\n"

#. "English Definition"
msgid "Term"
msgstr "Terme"

#. "To terminate abruptly a processing activity in a computer system because it is impossible or undesirable for the activity to procees."
msgid "abort"
msgstr "annuler"
"""

jtoolkit_extract = r"""
msgid ""
msgstr ""
"Project-Id-Version: PACKAGE VERSION\n"
"Report-Msgid-Bugs-To: \n"
"POT-Creation-Date: 2005-06-13 14:54-0500\n"
"PO-Revision-Date: 2007-05-04 19:54+0200\n"
"Last-Translator: F Wolff <friedel@translate.org.za>\n"
"Language-Team: LANGUAGE <LL@li.org>\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8bit\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\n"
"X-Generator: Pootle 1.0rc1\n"
"Generated-By: pygettext.py 1.5\n"

#: web/server.py:57
#, python-format
#, fuzzy
msgid "Login for %s"
msgstr "Meld aan vir %s"

#: web/server.py:91
msgid "Cancel this action and start a new session"
msgstr "Kanselleer hierdie aksie en begin 'n nuwe sessie"

#: web/server.py:92
msgid "Instead of confirming this action, log out and start from scratch"
msgstr "Meld af en begin op nuut eerder as om hierdie aksie te bevestig."

#: web/server.py:97
#, fuzzy
msgid "Exit application"
msgstr "Verlaat toepassing"

#: web/server.py:98
msgid "Exit this application and return to the parent application"
msgstr "Verlaat hierdie toepassing en gaan terug na die ouertoepassing"

#: web/server.py:105
msgid ", please confirm login"
msgstr ""
"""

def rm_rf(path):
    for dirpath, _, filenames in os.walk(path):
        for filename in filenames:
            os.remove(os.path.join(dirpath, filename))
    os.removedirs(path)

class TestStatsDb:
    def remove_dirs(self, path):
        if os.path.exists(path):
            rm_rf(path)

    def get_test_path(self, method):
        return os.path.realpath("%s_%s" % (self.__class__.__name__, method.__name__))

    def setup_method(self, method):
        """Allocates a unique self.filename for the method, making sure it doesn't exist"""
        self.path = self.get_test_path(method)
        self.remove_dirs(self.path)
        os.makedirs(self.path)

    def teardown_method(self, method):
        """Makes sure that if self.filename was created by the method, it is cleaned up"""
        self.remove_dirs(self.path)

    def setup_file_and_db(self, file_contents=fr_terminology_extract):
        cache = statsdb.StatsCache(os.path.join(self.path, "stats.db"))
        filename = os.path.join(self.path, "test.po")
        open(filename, "w").write(file_contents)
        f = factory.getobject(filename)
        return f, cache

    def test_getfileid_recache_cached_unit(self):
        """checks that a simple oo entry is parsed correctly"""
        checker = checks.UnitChecker()
        f, cache = self.setup_file_and_db()
        cache.filestats(f.filename, checker)
        state = cache.recacheunit(f.filename, checker, f.units[1])
        assert state == ['translated', 'total']

    def test_unitstats(self):
        f, cache = self.setup_file_and_db(jtoolkit_extract)
        u = cache.unitstats(f.filename)
        assert u['sourcewordcount'] == [3, 8, 11, 2, 9, 3]

    def test_filestats(self):
        f, cache = self.setup_file_and_db(jtoolkit_extract)
        s = cache.filestats(f.filename, checks.UnitChecker())
        assert s['translated'] == [2, 3, 5]
        assert s['fuzzy'] == [1, 4]
        assert s['untranslated'] == [6]
        assert s['total'] == [1, 2, 3, 4, 5, 6]

    def make_file_and_return_id(self, cache, filename):
        cache.cur.execute("""
            SELECT fileid, st_mtime, st_size FROM files
            WHERE path=?;""", (os.path.realpath(filename),))
        return cache.cur.fetchone()

    def test_if_cached_after_filestats(self):
        f, cache = self.setup_file_and_db(jtoolkit_extract)
        cache.filestats(f.filename, checks.UnitChecker())
        assert self.make_file_and_return_id(cache, f.filename) != None

    def test_if_cached_after_unitstats(self):
        f, cache = self.setup_file_and_db(jtoolkit_extract)
        cache.unitstats(f.filename, checks.UnitChecker())
        assert self.make_file_and_return_id(cache, f.filename) != None

    def test_singletonness(self):
        f1, cache1 = self.setup_file_and_db(jtoolkit_extract)
        f2, cache2 = self.setup_file_and_db(fr_terminology_extract)
        assert cache1 == cache2
