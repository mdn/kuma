from translate.misc import wStringIO
from translate.storage import rc, test_monolingual


def test_escaping():
    """test escaping Windows Resource files to Python strings"""
    assert rc.escape_to_python('''First line \
second line''') == "First line second line"
    assert rc.escape_to_python("A newline \\n in a string") == "A newline \n in a string"
    assert rc.escape_to_python("A tab \\t in a string") == "A tab \t in a string"
    assert rc.escape_to_python("A backslash \\\\ in a string") == "A backslash \\ in a string"
    assert rc.escape_to_python(r'''First line " \
 "second line''') == "First line second line"


class TestRcFile(object):
    StoreClass = rc.rcfile

    def source_parse(self, source):
        """Helper that parses source without requiring files."""
        dummy_file = wStringIO.StringIO(source)
        parsed_file = self.StoreClass(dummy_file)
        return parsed_file

    def source_regenerate(self, source):
        """Helper that converts source to store object and back."""
        return str(self.source_parse(source))

    def test_parse_only_comments(self):
        """Test parsing a RC string with only comments."""
        rc_source = """
/*
 * Mini test file.
 * Multiline comments.
 */

// Test file, one line comment. //

#include "other_file.h" // This must be ignored

LANGUAGE LANG_ENGLISH, SUBLANG_DEFAULT

/////////////////////////////////////////////////////////////////////////////
//
// Icon
//

// Icon with lowest ID value placed first to ensure application icon
// remains consistent on all systems.
IDR_MAINFRAME           ICON                    "res\\ico00007.ico"
IDR_MAINFRAME1          ICON                    "res\\idr_main.ico"
IDR_MAINFRAME2          ICON                    "res\\ico00006.ico"


/////////////////////////////////////////////////////////////////////////////
//
// Commented STRINGTABLE must be ignored
//

/*
STRINGTABLE
BEGIN
    IDP_REGISTRONOV         "Data isn't valid"
    IDS_ACTIVARINSTALACION  "You need to try again and again."
    IDS_NOREGISTRADO        "Error when making something important"
    IDS_REGISTRADO          "All done correctly.\nThank you very much."
    IDS_ACTIVADA            "This is what you do:\n%s"
    IDS_ERRORACTIV          "Error doing things"
END
*/

#ifndef APSTUDIO_INVOKED
/////////////////////////////////////////////////////////////////////////////
//
// Generated from the TEXTINCLUDE 3 resource.
//
#define _AFX_NO_SPLITTER_RESOURCES
#define _AFX_NO_OLE_RESOURCES
#define _AFX_NO_TRACKER_RESOURCES
#define _AFX_NO_PROPERTY_RESOURCES

#if !defined(AFX_RESOURCE_DLL) || defined(AFX_TARG_ESN)
// This will change the default language
LANGUAGE 10, 3
#pragma code_page(1252)
#include "res\regGHC.rc2"  // Recursos editados que no son de Microsoft Visual C++
#include "afxres.rc"         // Standar components
#endif

/////////////////////////////////////////////////////////////////////////////
#endif    // not APSTUDIO_INVOKED
"""
        rc_file = self.source_parse(rc_source)
        assert len(rc_file.units) == 0

    def test_parse_only_textinclude(self):
        """Test parsing a RC string with TEXTINCLUDE blocks and comments."""
        rc_source = """
#include "other_file.h" // This must be ignored

LANGUAGE LANG_ENGLISH, SUBLANG_DEFAULT

#ifdef APSTUDIO_INVOKED
/////////////////////////////////////////////////////////////////////////////
//
// TEXTINCLUDE
//

1 TEXTINCLUDE
BEGIN
    "resource.h\0"
END

2 TEXTINCLUDE
BEGIN
    "#include ""afxres.h""\r\n"
    "\0"
END

3 TEXTINCLUDE
BEGIN
    "LANGUAGE 10, 3\r\n"  // This language must be ignored, is a string.
    "And this strings don't need to be translated!"
END

#endif    // APSTUDIO_INVOKED
"""
        rc_file = self.source_parse(rc_source)
        assert len(rc_file.units) == 0

    def test_parse_dialog(self):
        """Test parsing a RC string with a DIALOG block."""
        rc_source = """
#include "other_file.h" // This must be ignored

LANGUAGE LANG_ENGLISH, SUBLANG_DEFAULT

/////////////////////////////////////////////////////////////////////////////
//
// Dialog
//

IDD_REGGHC_DIALOG DIALOGEX 0, 0, 211, 191
STYLE DS_SETFONT | DS_MODALFRAME | DS_FIXEDSYS | WS_POPUP | WS_VISIBLE | WS_CAPTION | WS_SYSMENU
EXSTYLE WS_EX_APPWINDOW
CAPTION "License dialog"
FONT 8, "MS Shell Dlg", 0, 0, 0x1
BEGIN
    PUSHBUTTON      "Help",ID_HELP,99,162,48,15
    PUSHBUTTON      "Close",IDCANCEL,151,162,48,15
    PUSHBUTTON      "Activate instalation",IDC_BUTTON1,74,76,76,18
    CTEXT           "My very good program",IDC_STATIC1,56,21,109,19,SS_SUNKEN
    CTEXT           "You can use it without registering it",IDC_STATIC,35,131,128,19,SS_SUNKEN
    PUSHBUTTON      "Offline",IDC_OFFLINE,149,108,42,13
    PUSHBUTTON      "See license",IDC_LICENCIA,10,162,85,15
    RTEXT           "If you don't have internet, please use magic.",IDC_STATIC,23,105,120,18
    ICON            IDR_MAINFRAME,IDC_STATIC,44,74,20,20
    CTEXT           "Use your finger to activate the program.",IDC_ACTIVADA,17,50,175,17
    ICON            IDR_MAINFRAME1,IDC_STATIC6,18,19,20,20
END
"""
        rc_file = self.source_parse(rc_source)
        assert len(rc_file.units) == 10
        rc_unit = rc_file.units[0]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.CAPTION"
        assert rc_unit.source == "License dialog"
        rc_unit = rc_file.units[1]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.PUSHBUTTON.ID_HELP"
        assert rc_unit.source == "Help"
        rc_unit = rc_file.units[2]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.PUSHBUTTON.IDCANCEL"
        assert rc_unit.source == "Close"
        rc_unit = rc_file.units[3]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.PUSHBUTTON.IDC_BUTTON1"
        assert rc_unit.source == "Activate instalation"
        rc_unit = rc_file.units[4]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.CTEXT.IDC_STATIC1"
        assert rc_unit.source == "My very good program"
        rc_unit = rc_file.units[5]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.CTEXT.IDC_STATIC"
        assert rc_unit.source == "You can use it without registering it"
        rc_unit = rc_file.units[6]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.PUSHBUTTON.IDC_OFFLINE"
        assert rc_unit.source == "Offline"
        rc_unit = rc_file.units[7]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.PUSHBUTTON.IDC_LICENCIA"
        assert rc_unit.source == "See license"
        rc_unit = rc_file.units[8]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.RTEXT.IDC_STATIC"
        assert rc_unit.source == "If you don't have internet, please use magic."
        rc_unit = rc_file.units[9]
        assert rc_unit.name == "DIALOGEX.IDD_REGGHC_DIALOG.CTEXT.IDC_ACTIVADA"
        assert rc_unit.source == "Use your finger to activate the program."

    def test_parse_stringtable(self):
        """Test parsing a RC string with a STRINGTABLE block."""
        rc_source = """
#include "other_file.h" // This must be ignored

LANGUAGE LANG_ENGLISH, SUBLANG_DEFAULT

/////////////////////////////////////////////////////////////////////////////
//
// String Table
//

STRINGTABLE
BEGIN
    IDP_REGISTRONOV         "Data isn't valid"
    IDS_ACTIVARINSTALACION  "You need to try again and again."
    IDS_NOREGISTRADO        "Error when making something important"
    IDS_REGISTRADO          "All done correctly.\nThank you very much."
    IDS_ACTIVADA            "This is what you do:\n%s"
    IDS_ERRORACTIV          "Error doing things"
END
"""
        rc_file = self.source_parse(rc_source)
        assert len(rc_file.units) == 6
        rc_unit = rc_file.units[0]
        assert rc_unit.name == "STRINGTABLE.IDP_REGISTRONOV"
        assert rc_unit.source == "Data isn't valid"
        rc_unit = rc_file.units[1]
        assert rc_unit.name == "STRINGTABLE.IDS_ACTIVARINSTALACION"
        assert rc_unit.source == "You need to try again and again."
        rc_unit = rc_file.units[2]
        assert rc_unit.name == "STRINGTABLE.IDS_NOREGISTRADO"
        assert rc_unit.source == "Error when making something important"
        rc_unit = rc_file.units[3]
        assert rc_unit.name == "STRINGTABLE.IDS_REGISTRADO"
        assert rc_unit.source == "All done correctly.\nThank you very much."
        rc_unit = rc_file.units[4]
        assert rc_unit.name == "STRINGTABLE.IDS_ACTIVADA"
        assert rc_unit.source == "This is what you do:\n%s"
        rc_unit = rc_file.units[5]
        assert rc_unit.name == "STRINGTABLE.IDS_ERRORACTIV"
        assert rc_unit.source == "Error doing things"
