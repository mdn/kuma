#!/usr/bin/env python
# -*- coding: utf-8 -*-

import warnings

from translate.misc import wStringIO
from translate.storage import oo


def test_makekey():
    """checks the makekey function for consistency"""
    assert oo.makekey(('project', r'path\to\the\sourcefile.src', 'resourcetype', 'GROUP_ID', 'LOCAL_ID', 'platform'), False) == "sourcefile.src#GROUP_ID.LOCAL_ID.resourcetype"
    # Testwith long_key i.e. used in multifile options
    assert oo.makekey(('project', r'path\to\the\sourcefile.src', 'resourcetype', 'GROUP_ID', 'LOCAL_ID', 'platform'), True) == "project/path/to/the/sourcefile.src#GROUP_ID.LOCAL_ID.resourcetype"
    assert oo.makekey(('project', r'path\to\the\sourcefile.src', 'resourcetype', 'GROUP_ID', '', 'platform'), False) == "sourcefile.src#GROUP_ID.resourcetype"
    assert oo.makekey(('project', r'path\to\the\sourcefile.src', 'resourcetype', '', 'LOCAL_ID', 'platform'), False) == "sourcefile.src#LOCAL_ID.resourcetype"
    assert oo.makekey(('project', r'path\to\the\sourcefile.src', '', 'GROUP_ID', 'LOCAL_ID', 'platform'), False) == "sourcefile.src#GROUP_ID.LOCAL_ID"
    assert oo.makekey(('project', r'path\to\the\sourcefile.src', '', 'GROUP_ID', '', 'platform'), False) == "sourcefile.src#GROUP_ID"


def test_escape_help_text():
    """Check the help text escape function"""
    assert oo.escape_help_text("If we don't know <tag> we don't <br> escape it") == "If we don't know <tag> we don't <br> escape it"
    # Bug 694
    assert oo.escape_help_text("A szó: <nyelv>") == "A szó: <nyelv>"
    assert oo.escape_help_text("""...következő: "<kiszolgáló> <témakör> <elem>", ahol...""") == """...következő: "<kiszolgáló> <témakör> <elem>", ahol..."""
    # See bug 694 comments 8-10 not fully resolved.
    assert oo.escape_help_text(r"...törtjel (\) létrehozásához...") == r"...törtjel (\\) létrehozásához..."


class TestOO:

    def setup_method(self, method):
        warnings.resetwarnings()

    def teardown_method(self, method):
        warnings.resetwarnings()

    def ooparse(self, oosource):
        """helper that parses oo source without requiring files"""
        dummyfile = wStringIO.StringIO(oosource)
        oofile = oo.oofile(dummyfile)
        return oofile

    def ooregen(self, oosource):
        """helper that converts oo source to oofile object and back"""
        return str(self.ooparse(oosource))

    def test_simpleentry(self):
        """checks that a simple oo entry is parsed correctly"""
        oosource = r'svx	source\dialog\numpages.src	0	string	RID_SVXPAGE_NUM_OPTIONS	STR_BULLET			0	en-US	Character				20050924 09:13:58'
        oofile = self.ooparse(oosource)
        assert len(oofile.units) == 1
        oe = oofile.units[0]
        assert oe.languages.keys() == ["en-US"]
        ol = oofile.oolines[0]
        assert ol.getkey() == ('svx', r'source\dialog\numpages.src', 'string', 'RID_SVXPAGE_NUM_OPTIONS', 'STR_BULLET', '')
        assert ol.text == 'Character'
        assert str(ol) == oosource

    def test_simpleentry_quickhelptest(self):
        """checks that a simple entry with quickhelptext is parsed correctly"""
        oosource = r'sd	source\ui\dlg\sdobjpal.src	0	imagebutton	FLTWIN_SDOBJPALETTE	BTN_SYMSIZE			16	en-US	-		Toggle Symbol Size		20051017 21:40:56'
        oofile = self.ooparse(oosource)
        assert len(oofile.units) == 1
        oe = oofile.units[0]
        assert oe.languages.keys() == ["en-US"]
        ol = oofile.oolines[0]
        assert ol.getkey() == ('sd', r'source\ui\dlg\sdobjpal.src', 'imagebutton', 'FLTWIN_SDOBJPALETTE', 'BTN_SYMSIZE', '')
        assert ol.quickhelptext == 'Toggle Symbol Size'
        assert str(ol) == oosource

    def test_simpleentry_title(self):
        """checks that a simple entry with title text is parsed correctly"""
        oosource = r'dbaccess	source\ui\dlg\indexdialog.src	0	querybox	QUERY_SAVE_CURRENT_INDEX				0	en-US	Do you want to save the changes made to the current index?			Exit Index Design	20051017 21:40:56'
        oofile = self.ooparse(oosource)
        assert len(oofile.units) == 1
        oe = oofile.units[0]
        assert oe.languages.keys() == ["en-US"]
        ol = oofile.oolines[0]
        assert ol.getkey() == ('dbaccess', r'source\ui\dlg\indexdialog.src', 'querybox', 'QUERY_SAVE_CURRENT_INDEX', '', '')
        assert ol.title == 'Exit Index Design'
        assert str(ol) == oosource

    def test_blankline(self):
        """checks that a blank line is parsed correctly"""
        oosource = '\n'
        warnings.simplefilter("error")
        oofile = self.ooparse(oosource)
        assert len(oofile.units) == 0

    def test_fieldlength(self):
        """checks that we process the length field correctly"""
        # Since the actual field is 18 characters long and the field width in this example is 16 we're not sure if they even use this!
        oosource = r'sd	source\ui\dlg\sdobjpal.src	0	imagebutton	FLTWIN_SDOBJPALETTE	BTN_SYMSIZE			16	en-US	-		Toggle Symbol Size		20051017 21:40:56'
        oofile = self.ooparse(oosource)
        assert len(oofile.units) == 1
        oe = oofile.units[0]
        assert oe.languages.keys() == ["en-US"]
        ol = oofile.oolines[0]
        assert int(ol.width) == 16

    def test_escapes(self):
        """checks that we escape properly"""
        oosource = r'svx	source\dialog\numpages.src	0	string	RID_SVXPAGE_NUM_OPTIONS	STR_BULLET			0	en-US	size *2 \\langle x \\rangle				20050924 09:13:58'
        oofile = self.ooregen(oosource)
        assert r'size *2 \\langle x \\rangle' in oofile
