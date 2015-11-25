# -*- coding: utf-8 -*-

"""tests decoration handling functions that are used by checks"""

from translate.filters import decoration


def test_spacestart():
    """test operation of spacestart()"""
    assert decoration.spacestart("  Start") == "  "
    assert decoration.spacestart(u"\u0020\u00a0Start") == u"\u0020\u00a0"
    # non-breaking space
    assert decoration.spacestart(u"\u00a0\u202fStart") == u"\u00a0\u202f"
    # Some exotic spaces
    assert decoration.spacestart(u"\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200aStart") == u"\u2000\u2001\u2002\u2003\u2004\u2005\u2006\u2007\u2008\u2009\u200a"


def test_isvalidaccelerator():
    """test the isvalidaccelerator() function"""
    # Mostly this tests the old code path where acceptlist is None
    assert not decoration.isvalidaccelerator(u"")
    assert decoration.isvalidaccelerator(u"a")
    assert decoration.isvalidaccelerator(u"1")
    assert not decoration.isvalidaccelerator(u"ḽ")
    # Test new code path where we actually have an acceptlist
    assert decoration.isvalidaccelerator(u"a", u"aeiou")
    assert decoration.isvalidaccelerator(u"ḽ", u"ḓṱḽṋṅ")
    assert not decoration.isvalidaccelerator(u"a", u"ḓṱḽṋṅ")


def test_find_marked_variables():
    """check that we can identify variables correctly, the first returned
    value is the start location, the second returned value is the actual
    variable sans decoations"""
    variables = decoration.findmarkedvariables("The <variable> string", "<", ">")
    assert variables == [(4, "variable")]
    variables = decoration.findmarkedvariables("The $variable string", "$", 1)
    assert variables == [(4, "v")]
    variables = decoration.findmarkedvariables("The $variable string", "$", None)
    assert variables == [(4, "variable")]
    variables = decoration.findmarkedvariables("The $variable string", "$", 0)
    assert variables == [(4, "")]
    variables = decoration.findmarkedvariables("The &variable; string", "&", ";")
    assert variables == [(4, "variable")]
    variables = decoration.findmarkedvariables("The &variable.variable; string", "&", ";")
    assert variables == [(4, "variable.variable")]


def test_getnumbers():
    """test operation of getnumbers()"""
    assert decoration.getnumbers(u"") == []
    assert decoration.getnumbers(u"No numbers") == []
    assert decoration.getnumbers(u"Nine 9 nine") == ["9"]
    assert decoration.getnumbers(u"Two numbers: 2 and 3") == ["2", "3"]
    assert decoration.getnumbers(u"R5.99") == ["5.99"]
    # TODO fix these so that we are able to consider locale specific numbers
    #assert decoration.getnumbers(u"R5,99") == ["5.99"]
    #assert decoration.getnumbers(u"1\u00a0000,99") == ["1000.99"]
    assert decoration.getnumbers(u"36°") == [u"36°"]
    assert decoration.getnumbers(u"English 123, Bengali \u09e7\u09e8\u09e9") == [u"123", u"\u09e7\u09e8\u09e9"]


def test_getfunctions():
    """test operation of getfunctions()"""
    assert decoration.getfunctions(u"") == []
    assert decoration.getfunctions(u"There is no function") == []
    assert decoration.getfunctions(u"Use the getfunction() function.") == ["getfunction()"]
    assert decoration.getfunctions(u"Use the getfunction1() function or the getfunction2() function.") == ["getfunction1()", "getfunction2()"]
    assert decoration.getfunctions(u"The module.getfunction() method") == ["module.getfunction()"]
    assert decoration.getfunctions(u"The module->getfunction() method") == ["module->getfunction()"]
    assert decoration.getfunctions(u"The module::getfunction() method") == ["module::getfunction()"]
    assert decoration.getfunctions(u"The function().function() function") == ["function().function()"]
    assert decoration.getfunctions(u"Deprecated, use function().") == ["function()"]
    assert decoration.getfunctions(u"Deprecated, use function() or other().") == ["function()", "other()"]
