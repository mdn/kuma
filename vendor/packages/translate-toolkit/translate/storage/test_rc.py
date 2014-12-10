from translate.storage import rc

def test_escaping():
    """test escaping Windows Resource files to Python strings"""
    assert rc.escape_to_python('''First line \
second line''') == "First line second line"
    assert rc.escape_to_python("A newline \\n in a string") == "A newline \n in a string"
    assert rc.escape_to_python("A tab \\t in a string") == "A tab \t in a string"
    assert rc.escape_to_python("A backslash \\\\ in a string") == "A backslash \\ in a string"
    assert rc.escape_to_python(r'''First line " \
 "second line''') == "First line second line"
