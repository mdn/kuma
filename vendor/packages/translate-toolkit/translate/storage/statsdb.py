#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2009 Zuza Software Foundation
#
# This file is part of the Translate Toolkit.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.


"""Module to provide a cache of statistics in a database.

@organization: Zuza Software Foundation
@copyright: 2007 Zuza Software Foundation
@license: U{GPL <http://www.fsf.org/licensing/licenses/gpl.html>}
"""

from UserDict import UserDict

from translate import __version__ as toolkitversion
from translate.storage import factory
from translate.misc.multistring import multistring
from translate.lang.common import Common

try:
    from sqlite3 import dbapi2
except ImportError:
    from pysqlite2 import dbapi2
import os.path
import re
import sys
import stat
import thread

kdepluralre = re.compile("^_n: ")
brtagre = re.compile("<br\s*?/?>")
xmltagre = re.compile("<[^>]+>")
numberre = re.compile("\\D\\.\\D")

state_strings = {0: "untranslated", 1: "translated", 2: "fuzzy"}

def wordcount(string):
    # TODO: po class should understand KDE style plurals
    string = kdepluralre.sub("", string)
    string = brtagre.sub("\n", string)
    string = xmltagre.sub("", string)
    string = numberre.sub(" ", string)
    #TODO: This should still use the correct language to count in the target
    #language
    return len(Common.words(string))

def wordsinunit(unit):
    """Counts the words in the unit's source and target, taking plurals into
    account. The target words are only counted if the unit is translated."""
    (sourcewords, targetwords) = (0, 0)
    if isinstance(unit.source, multistring):
        sourcestrings = unit.source.strings
    else:
        sourcestrings = [unit.source or ""]
    for s in sourcestrings:
        sourcewords += wordcount(s)
    if not unit.istranslated():
        return sourcewords, targetwords
    if isinstance(unit.target, multistring):
        targetstrings = unit.target.strings
    else:
        targetstrings = [unit.target or ""]
    for s in targetstrings:
        targetwords += wordcount(s)
    return sourcewords, targetwords

class Record(UserDict):
    def __init__(self, record_keys, record_values=None, compute_derived_values = lambda x: x):
        if record_values == None:
            record_values = (0 for _i in record_keys)
        self.record_keys = record_keys
        self.data = dict(zip(record_keys, record_values))
        self._compute_derived_values = compute_derived_values
        self._compute_derived_values(self)

    def to_tuple(self):
        return tuple(self[key] for key in self.record_keys)

    def __add__(self, other):
        result = Record(self.record_keys)
        for key in self.keys():
            result[key] = self[key] + other[key]
        self._compute_derived_values(self)
        return result

    def __sub__(self, other):
        result = Record(self.record_keys)
        for key in self.keys():
            result[key] = self[key] - other[key]
        self._compute_derived_values(self)
        return result

    def as_string_for_db(self):
        return ",".join([repr(x) for x in self.to_tuple()])

def transaction(f):
    """Modifies f to commit database changes if it executes without exceptions.
    Otherwise it rolls back the database.

    ALL publicly accessible methods in StatsCache MUST be decorated with this
    decorator.
    """

    def decorated_f(self, *args, **kwargs):
        try:
            result = f(self, *args, **kwargs)
            self.con.commit()
            return result
        except:
            # If ANY exception is raised, we're left in an
            # uncertain state and we MUST roll back any changes to avoid getting
            # stuck in an inconsistent state.
            if self.con:
                self.con.rollback()
            raise
    return decorated_f

UNTRANSLATED, TRANSLATED, FUZZY = 0, 1, 2
def statefordb(unit):
    """Returns the numeric database state for the unit."""
    if unit.istranslated():
        return TRANSLATED
    if unit.isfuzzy() and unit.target:
        return FUZZY
    return UNTRANSLATED

class FileTotals(object):
    keys = ['translatedsourcewords',
            'fuzzysourcewords',
            'untranslatedsourcewords',
            'translated',
            'fuzzy',
            'untranslated',
            'translatedtargetwords']

    def db_keys(self):
        return ",".join(self.keys)

    def __init__(self, cur):
        self.cur = cur
        self.cur.execute("""
            CREATE TABLE IF NOT EXISTS filetotals(
                fileid                  INTEGER PRIMARY KEY AUTOINCREMENT,
                translatedsourcewords   INTEGER NOT NULL,
                fuzzysourcewords        INTEGER NOT NULL,
                untranslatedsourcewords INTEGER NOT NULL,
                translated              INTEGER NOT NULL,
                fuzzy                   INTEGER NOT NULL,
                untranslated            INTEGER NOT NULL,
                translatedtargetwords   INTEGER NOT NULL);""")

    def new_record(cls, state_for_db=None, sourcewords=None, targetwords=None):
        record = Record(cls.keys, compute_derived_values = cls._compute_derived_values)
        if state_for_db is not None:
            if state_for_db is UNTRANSLATED:
                record['untranslated'] = 1
                record['untranslatedsourcewords'] = sourcewords
            if state_for_db is TRANSLATED:
                record['translated'] = 1
                record['translatedsourcewords'] = sourcewords
                record['translatedtargetwords'] = targetwords
            elif state_for_db is FUZZY:
                record['fuzzy'] = 1
                record['fuzzysourcewords'] = sourcewords
        return record

    new_record = classmethod(new_record)

    def _compute_derived_values(cls, record):
        record["total"]            = record["untranslated"] + \
                                     record["translated"] + \
                                     record["fuzzy"]
        record["totalsourcewords"] = record["untranslatedsourcewords"] + \
                                     record["translatedsourcewords"] + \
                                     record["fuzzysourcewords"]
        record["review"]           = 0
    _compute_derived_values = classmethod(_compute_derived_values)

    def __getitem__(self, fileid):
        result = self.cur.execute("""
            SELECT %(keys)s
            FROM   filetotals
            WHERE  fileid=?;""" % {'keys': self.db_keys()}, (fileid,))
        return Record(FileTotals.keys, result.fetchone(), self._compute_derived_values)

    def __setitem__(self, fileid, record):
        self.cur.execute("""
            INSERT OR REPLACE into filetotals
            VALUES (%(fileid)d, %(vals)s);
        """ % {'fileid': fileid, 'vals': record.as_string_for_db()})

    def __delitem__(self, fileid):
        self.cur.execute("""
            DELETE FROM filetotals
            WHERE fileid=?;
        """,  (fileid,))

def emptyfiletotals():
    """Returns a dictionary with all statistics initalised to 0."""
    return FileTotals.new_record()

def emptyfilechecks():
    return {}

def emptyfilestats():
    return {"total": [], "translated": [], "fuzzy": [], "untranslated": []}

def emptyunitstats():
    return {"sourcewordcount": [], "targetwordcount": []}

# We allow the caller to specify which value to return when errors_return_empty
# is True. We do this, since Poolte wants None to be returned when it calls
# get_mod_info directly, whereas we want an integer to be returned for
# uses of get_mod_info within this module.
# TODO: Get rid of empty_return when Pootle code is improved to not require
#       this.
def get_mod_info(file_path):
    file_stat = os.stat(file_path)
    assert not stat.S_ISDIR(file_stat.st_mode)
    return file_stat.st_mtime, file_stat.st_size

def suggestion_extension():
    return os.path.extsep + 'pending'

def suggestion_filename(filename):
    return filename + suggestion_extension()

# ALL PUBLICLY ACCESSIBLE METHODS MUST BE DECORATED WITH THE transaction DECORATOR.
class StatsCache(object):
    """An object instantiated as a singleton for each statsfile that provides
    access to the database cache from a pool of StatsCache objects."""
    _caches = {}
    defaultfile = None
    con = None
    """This cache's connection"""
    cur = None
    """The current cursor"""

    def __new__(cls, statsfile=None):
        current_thread = thread.get_ident()
        def make_database(statsfile):
            def connect(cache):
                cache.con = dbapi2.connect(statsfile)
                cache.cur = cache.con.cursor()

            def clear_old_data(cache):
                try:
                    cache.cur.execute("""SELECT toolkitbuild FROM files""")
                    val = cache.cur.fetchone()
                    # If the database is empty, we have no idea whether its layout
                    # is correct, so we might as well delete it.
                    if val is None or val[0] < toolkitversion.build:
                        cache.con.close()
                        del cache
                        os.unlink(statsfile)
                        return True
                    return False
                except dbapi2.OperationalError:
                    return False
            
            cache = cls._caches.setdefault(current_thread, {})[statsfile] = object.__new__(cls)
            connect(cache)
            if clear_old_data(cache):
                connect(cache)
            cache.create()
            return cache

        if not statsfile:
            if not cls.defaultfile:
                userdir = os.path.expanduser("~")
                cachedir = None
                if os.name == "nt":
                    cachedir = os.path.join(userdir, "Translate Toolkit")
                else:
                    cachedir = os.path.join(userdir, ".translate_toolkit")
                if not os.path.exists(cachedir):
                    os.mkdir(cachedir)
                cls.defaultfile = os.path.realpath(os.path.join(cachedir, "stats.db"))
            statsfile = cls.defaultfile
        else:
            statsfile = os.path.realpath(statsfile)
        # First see if a cache for this file already exists:
        if current_thread in cls._caches and statsfile in cls._caches[current_thread]:
            return cls._caches[current_thread][statsfile]
        # No existing cache. Let's build a new one and keep a copy
        return make_database(statsfile)

    @transaction
    def create(self):
        """Create all tables and indexes."""
        self.file_totals = FileTotals(self.cur)

        self.cur.execute("""CREATE TABLE IF NOT EXISTS files(
            fileid INTEGER PRIMARY KEY AUTOINCREMENT,
            path VARCHAR NOT NULL UNIQUE,
            st_mtime INTEGER NOT NULL,
            st_size INTEGER NOT NULL,
            toolkitbuild INTEGER NOT NULL);""")

        self.cur.execute("""CREATE UNIQUE INDEX IF NOT EXISTS filepathindex
            ON files (path);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS units(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            unitid VARCHAR NOT NULL,
            fileid INTEGER NOT NULL,
            unitindex INTEGER NOT NULL,
            source VARCHAR NOT NULL,
            target VARCHAR,
            state INTEGER,
            sourcewords INTEGER,
            targetwords INTEGER);""")

        self.cur.execute("""CREATE INDEX IF NOT EXISTS fileidindex
            ON units(fileid);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS checkerconfigs(
            configid INTEGER PRIMARY KEY AUTOINCREMENT,
            config VARCHAR);""")

        self.cur.execute("""CREATE INDEX IF NOT EXISTS configindex
            ON checkerconfigs(config);""")

        self.cur.execute("""CREATE TABLE IF NOT EXISTS uniterrors(
            errorid INTEGER PRIMARY KEY AUTOINCREMENT,
            unitindex INTEGER NOT NULL,
            fileid INTEGER NOT NULL,
            configid INTEGER NOT NULL,
            name VARCHAR NOT NULL,
            message VARCHAR);""")

        self.cur.execute("""CREATE INDEX IF NOT EXISTS uniterrorindex
            ON uniterrors(fileid, configid);""")

    @transaction
    def _getfileid(self, filename, check_mod_info=True, store=None):
        """return fileid representing the given file in the statscache.

        if file not in cache or has been updated since last record
        update, recalculate stats.

        optional argument store can be used to avoid unnessecary
        reparsing of already loaded translation files.

        store can be a TranslationFile object or a callback that returns one.
        """
        if isinstance(filename, str):
            filename = unicode(filename, sys.getfilesystemencoding())
        realpath = os.path.realpath(filename)
        self.cur.execute("""SELECT fileid, st_mtime, st_size FROM files
                WHERE path=?;""", (realpath,))
        filerow = self.cur.fetchone()
        mod_info = get_mod_info(realpath)
        if filerow:
            fileid = filerow[0]
            if not check_mod_info:
                # Update the mod_info of the file
                self.cur.execute("""UPDATE files
                        SET st_mtime=?, st_size=?
                        WHERE fileid=?;""", (mod_info[0], mod_info[1], fileid))
                return fileid
            if (filerow[1], filerow[2]) == mod_info:
                return fileid

        # file wasn't in db at all, lets recache it
        if callable(store):
            store = store()
        else:
            store = store or factory.getobject(realpath)

        return self._cachestore(store, realpath, mod_info)
    
    def _getstoredcheckerconfig(self, checker):
        """See if this checker configuration has been used before."""
        config = str(checker.config.__dict__)
        self.cur.execute("""SELECT configid, config FROM checkerconfigs WHERE
            config=?;""", (config,))
        configrow = self.cur.fetchone()
        if not configrow or configrow[1] != config:
            return None
        else:
            return configrow[0]

    @transaction
    def _cacheunitstats(self, units, fileid, unitindex=None, file_totals_record=FileTotals.new_record()):
        """Cache the statistics for the supplied unit(s)."""
        unitvalues = []
        for index, unit in enumerate(units):
            if unit.istranslatable():
                sourcewords, targetwords = wordsinunit(unit)
                if unitindex:
                    index = unitindex
                # what about plurals in .source and .target?
                unitvalues.append((unit.getid(), fileid, index, \
                                unit.source, unit.target, \
                                sourcewords, targetwords, \
                                statefordb(unit)))
                file_totals_record = file_totals_record + FileTotals.new_record(statefordb(unit), sourcewords, targetwords)
        # XXX: executemany is non-standard
        self.cur.executemany("""INSERT INTO units
            (unitid, fileid, unitindex, source, target, sourcewords, targetwords, state)
            values (?, ?, ?, ?, ?, ?, ?, ?);""",
            unitvalues)
        self.file_totals[fileid] = file_totals_record
        if unitindex:
            return state_strings[statefordb(units[0])]
        return ""

    @transaction
    def _cachestore(self, store, realpath, mod_info):
        """Calculates and caches the statistics of the given store
        unconditionally."""
        self.cur.execute("""DELETE FROM files WHERE
            path=?;""", (realpath,))
        self.cur.execute("""INSERT INTO files
            (fileid, path, st_mtime, st_size, toolkitbuild) values (NULL, ?, ?, ?, ?);""",
            (realpath, mod_info[0], mod_info[1], toolkitversion.build))
        fileid = self.cur.lastrowid
        self.cur.execute("""DELETE FROM units WHERE
            fileid=?""", (fileid,))
        self._cacheunitstats(store.units, fileid)
        return fileid

    def filetotals(self, filename, store=None):
        """Retrieves the statistics for the given file if possible, otherwise
        delegates to cachestore()."""
        return self.file_totals[self._getfileid(filename, store=store)]

    @transaction
    def _cacheunitschecks(self, units, fileid, configid, checker, unitindex=None):
        """Helper method for cachestorechecks() and recacheunit()"""
        # We always want to store one dummy error to know that we have actually
        # run the checks on this file with the current checker configuration
        dummy = (-1, fileid, configid, "noerror", "")
        unitvalues = [dummy]
        # if we are doing a single unit, we want to return the checknames
        errornames = []
        for index, unit in enumerate(units):
            if unit.istranslatable():
                # Correctly assign the unitindex
                if unitindex:
                    index = unitindex
                failures = checker.run_filters(unit)
                for checkname, checkmessage in failures.iteritems():
                    unitvalues.append((index, fileid, configid, checkname, checkmessage))
                    errornames.append("check-" + checkname)
        checker.setsuggestionstore(None)

        if unitindex:
            # We are only updating a single unit, so we don't want to add an
            # extra noerror-entry
            unitvalues.remove(dummy)
            errornames.append("total")

        # XXX: executemany is non-standard
        self.cur.executemany("""INSERT INTO uniterrors
            (unitindex, fileid, configid, name, message)
            values (?, ?, ?, ?, ?);""",
            unitvalues)
        return errornames

    @transaction
    def _cachestorechecks(self, fileid, store, checker, configid):
        """Calculates and caches the error statistics of the given store
        unconditionally."""
        # Let's purge all previous failures because they will probably just
        # fill up the database without much use.
        self.cur.execute("""DELETE FROM uniterrors WHERE
            fileid=?;""", (fileid,))
        self._cacheunitschecks(store.units, fileid, configid, checker)
        return fileid

    def get_unit_stats(self, fileid, unitid):
        values = self.cur.execute("""
            SELECT   state, sourcewords, targetwords
            FROM     units
            WHERE    fileid=? AND unitid=?
        """, (fileid, unitid))
        result = values.fetchone()
        if result is not None:
            return result
        else:
            print >> sys.stderr, """WARNING: Database in inconsistent state. 
            fileid %d and unitid %s have no entries in the table units.""" % (fileid, unitid)
            # If values.fetchone() is None, then we return an empty list,
            # to make FileTotals.new_record(*self.get_unit_stats(fileid, unitid))
            # do the right thing.
            return []

    @transaction
    def recacheunit(self, filename, checker, unit):
        """Recalculate all information for a specific unit. This is necessary
        for updating all statistics when a translation of a unit took place,
        for example.

        This method assumes that everything was up to date before (file totals,
        checks, checker config, etc."""
        fileid = self._getfileid(filename, check_mod_info=False)
        configid = self._get_config_id(fileid, checker)
        unitid = unit.getid()
        # get the unit index
        totals_without_unit = self.file_totals[fileid] - \
                                   FileTotals.new_record(*self.get_unit_stats(fileid, unitid))
        self.cur.execute("""SELECT unitindex FROM units WHERE
            fileid=? AND unitid=?;""", (fileid, unitid))
        unitindex = self.cur.fetchone()[0]
        self.cur.execute("""DELETE FROM units WHERE
            fileid=? AND unitid=?;""", (fileid, unitid))
        state = [self._cacheunitstats([unit], fileid, unitindex, totals_without_unit)]
        # remove the current errors
        self.cur.execute("""DELETE FROM uniterrors WHERE
            fileid=? AND unitindex=?;""", (fileid, unitindex))
        if os.path.exists(suggestion_filename(filename)):
            checker.setsuggestionstore(factory.getobject(suggestion_filename(filename), ignore=suggestion_extension()))
        state.extend(self._cacheunitschecks([unit], fileid, configid, checker, unitindex))
        return state

    def _checkerrors(self, filename, fileid, configid, checker, store):
        def geterrors():
            self.cur.execute("""SELECT
                name,
                unitindex
                FROM uniterrors WHERE fileid=? and configid=?
                ORDER BY unitindex;""", (fileid, configid))
            return self.cur.fetchone(), self.cur

        first, cur = geterrors()
        if first is not None:
            return first, cur

        # This could happen if we haven't done the checks before, or the
        # file changed, or we are using a different configuration
        if callable(store):
            store = store()
        else:
            store = store or factory.getobject(filename)

        if os.path.exists(suggestion_filename(filename)):
            checker.setsuggestionstore(factory.getobject(suggestion_filename(filename), ignore=suggestion_extension()))
        self._cachestorechecks(fileid, store, checker, configid)
        return geterrors()

    def _geterrors(self, filename, fileid, configid, checker, store):
        result = []
        first, cur = self._checkerrors(filename, fileid, configid, checker, store)
        result.append(first)
        result.extend(cur.fetchall())
        return result

    @transaction
    def _get_config_id(self, fileid, checker):
        configid = self._getstoredcheckerconfig(checker)
        if configid:
            return configid
        self.cur.execute("""INSERT INTO checkerconfigs
            (configid, config) values (NULL, ?);""",
            (str(checker.config.__dict__),))
        return self.cur.lastrowid

    def filechecks(self, filename, checker, store=None):
        """Retrieves the error statistics for the given file if possible,
        otherwise delegates to cachestorechecks()."""
        fileid = self._getfileid(filename, store=store)
        configid = self._get_config_id(fileid, checker)
        values = self._geterrors(filename, fileid, configid, checker, store)

        errors = emptyfilechecks()
        for value in values:
            if value[1] == -1:
                continue
            checkkey = 'check-' + value[0]      #value[0] is the error name
            if not checkkey in errors:
                errors[checkkey] = []
            errors[checkkey].append(value[1])   #value[1] is the unitindex

        return errors

    def file_fails_test(self, filename, checker, name):
        fileid = self._getfileid(filename)
        configid = self._get_config_id(fileid, checker) 
        self._checkerrors(filename, fileid, configid, checker, None)
        self.cur.execute("""SELECT
            name,
            unitindex
            FROM uniterrors 
            WHERE fileid=? and configid=? and name=?;""", (fileid, configid, name))
        return self.cur.fetchone() is not None

    def filestatestats(self, filename, store=None):
        """Return a dictionary of unit stats mapping sets of unit
        indices with those states"""
        stats = emptyfilestats()
        fileid = self._getfileid(filename, store=store)

        self.cur.execute("""SELECT
            state,
            unitindex
            FROM units WHERE fileid=?
            ORDER BY unitindex;""", (fileid,))
        values = self.cur.fetchall()

        for value in values:
            stats[state_strings[value[0]]].append(value[1])
            stats["total"].append(value[1])

        return stats

    def filestats(self, filename, checker, store=None):
        """Return a dictionary of property names mapping sets of unit
        indices with those properties."""
        stats = emptyfilestats()
        stats.update(self.filechecks(filename, checker, store))
        stats.update(self.filestatestats(filename, store))
        return stats

    def unitstats(self, filename, _lang=None, store=None):
        # For now, lang and store are unused. lang will allow the user to
        # base stats information on the given language. See the commented
        # line containing stats.update below.
        """Return a dictionary of property names mapping to arrays which
        map unit indices to property values.

        Please note that this is different from filestats, since filestats
        supplies sets of unit indices with a given property, whereas this
        method supplies arrays which map unit indices to given values."""
        stats = emptyunitstats()

        #stats.update(self.unitchecks(filename, lang, store))
        fileid = self._getfileid(filename, store=store)

        self.cur.execute("""SELECT
          sourcewords, targetwords
          FROM units WHERE fileid=?
          ORDER BY unitindex;""", (fileid,))

        for sourcecount, targetcount in self.cur.fetchall():
            stats["sourcewordcount"].append(sourcecount)
            stats["targetwordcount"].append(targetcount)

        return stats
