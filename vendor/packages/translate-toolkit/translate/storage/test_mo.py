#!/usr/bin/env python

import StringIO
import subprocess
import os.path

from translate.storage import test_base
from translate.storage import mo
from translate.storage import factory

class TestMOUnit(test_base.TestTranslationUnit):
    UnitClass = mo.mounit

posources = [
r'''
msgid ""
msgstr ""
"PO-Revision-Date: 2006-02-09 23:33+0200\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8-bit\n"
''',
r'''
msgid ""
msgstr ""
"PO-Revision-Date: 2006-02-09 23:33+0200\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8-bit\n"

msgid "plant"
msgstr ""
''',
# The following test is commented out, because the hash-size is different
# compared to gettext, since we're not counting untranslated units.
#r'''
#msgid ""
#msgstr ""
#"PO-Revision-Date: 2006-02-09 23:33+0200\n"
#"MIME-Version: 1.0\n"
#"Content-Type: text/plain; charset=UTF-8\n"
#"Content-Transfer-Encoding: 8-bit\n"
#
#msgid "plant"
#msgstr ""
#
#msgid ""
#"_: Noun\n"
#"convert"
#msgstr "bekeerling"
#''',
r'''
msgid ""
msgstr ""
"PO-Revision-Date: 2006-02-09 23:33+0200\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8-bit\n"

msgid "plant"
msgstr ""

msgid ""
"_: Noun\n"
"convert"
msgstr "bekeerling"

msgctxt "verb"
msgid ""
"convert"
msgstr "omskakel"
''',
r'''
msgid ""
msgstr ""
"PO-Revision-Date: 2006-02-09 23:33+0200\n"
"MIME-Version: 1.0\n"
"Content-Type: text/plain; charset=UTF-8\n"
"Content-Transfer-Encoding: 8-bit\n"

msgid "plant"
msgstr ""

msgid ""
"_: Noun\n"
"convert"
msgstr "bekeerling"

msgctxt "verb"
msgid ""
"convert"
msgstr "omskakel"

msgid "tree"
msgid_plural "trees"
msgstr[0] ""
''']

class TestMOFile(test_base.TestTranslationStore):
    StoreClass = mo.mofile

    def get_mo_and_po(self):
        return (os.path.abspath(self.filename + '.po'),
                os.path.abspath(self.filename + '.msgfmt.mo'),
                os.path.abspath(self.filename + '.pocompile.mo'))

    def remove_po_and_mo(self):
        for file in self.get_mo_and_po():
            if os.path.exists(file):
                os.remove(file)

    def setup_method(self, method):
        test_base.TestTranslationStore.setup_method(self, method)
        self.remove_po_and_mo()

    def teardown_method(self, method):
        test_base.TestTranslationStore.teardown_method(self, method)
        self.remove_po_and_mo()

    def test_output(self):
        for posource in posources:
            print "PO source file"
            print posource
            PO_FILE, MO_MSGFMT, MO_POCOMPILE = self.get_mo_and_po()

            out_file = open(PO_FILE, 'w')
            out_file.write(posource)
            out_file.close()

            subprocess.call(['msgfmt', PO_FILE, '-o', MO_MSGFMT])
            subprocess.call(['pocompile', PO_FILE, MO_POCOMPILE])

            store = factory.getobject(StringIO.StringIO(posource))
            if store.isempty() and not os.path.exists(MO_POCOMPILE):
                # pocompile doesn't create MO files for empty PO files, so we
                # can skip the checks here.
                continue

            mo_msgfmt_f = open(MO_MSGFMT)
            mo_pocompile_f = open(MO_POCOMPILE)

            try:
                mo_msgfmt = mo_msgfmt_f.read()
                print "msgfmt output:"
                print repr(mo_msgfmt)
                mo_pocompile = mo_pocompile_f.read()
                print "pocompile output:"
                print repr(mo_pocompile)
                assert mo_msgfmt == mo_pocompile
            finally:
                mo_msgfmt_f.close()
                mo_pocompile_f.close()
