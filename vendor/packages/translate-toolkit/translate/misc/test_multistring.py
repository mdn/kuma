#!/usr/bin/env python

from translate.misc import multistring
from translate.misc import test_autoencode

class TestMultistring(test_autoencode.TestAutoencode):
    type2test = multistring.multistring

    def test_constructor(self):
        t = self.type2test
        s1 = t("test")
        assert type(s1) == t
        assert s1 == "test"
        assert s1.strings == ["test"]
        s2 = t(["test", "me"])
        assert type(s2) == t
        assert s2 == "test"
        assert s2.strings == ["test", "me"]
        assert s2 != s1

    def test_replace(self):
        t = self.type2test
        s1 = t(["abcdef", "def"])

        result = s1.replace("e", "")
        assert type(result) == t
        assert result == t(["abcdf", "df"])

        result = s1.replace("e", "xx")
        assert result == t(["abcdxxf", "dxxf"])

        result = s1.replace("e", u"\xe9")
        assert result == t([u"abcd\xe9f", u"d\xe9f"])

	result = s1.replace("e", "\n")
	assert result == t([u"abcd\nf", u"d\nf"])

	result = result.replace("\n", "\\n")
	assert result == t([u"abcd\\nf", u"d\\nf"])
	
	result = result.replace("\\n", "\n")
	assert result == t([u"abcd\nf", u"d\nf"])
