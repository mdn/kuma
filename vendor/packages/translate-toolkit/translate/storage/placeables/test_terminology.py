#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from StringIO import StringIO

from translate.search.match import terminologymatcher
from translate.storage.pypo import pofile
from translate.storage.placeables import base, general, parse, StringElem
from translate.storage.placeables.terminology import parsers as term_parsers, TerminologyPlaceable


class TestTerminologyPlaceable:
    TERMINOLOGY = """
msgid "name"
msgstr "naam"

msgid "file"
msgstr "lêer"

msgid "file name th"
msgstr "lêernaam wat?"

msgid "file name"
msgstr "lêernaam"
"""

    def setup_method(self, method):
        self.term_po = pofile(StringIO(self.TERMINOLOGY))
        self.matcher = terminologymatcher(self.term_po)
        self.test_string = u'<b>Inpüt</b> file name thingy.'

    def test_simple_terminology(self):
        TerminologyPlaceable.matchers = [self.matcher]
        tree = parse(self.test_string, general.parsers + term_parsers)

        assert isinstance(tree.sub[0], general.XMLTagPlaceable)
        assert isinstance(tree.sub[2], general.XMLTagPlaceable)

        tree.print_tree()
        term = tree.sub[3].sub[1]

        assert isinstance(term, TerminologyPlaceable)
        assert unicode(term) == self.term_po.getunits()[2].source
        assert term.translate() == unicode(self.term_po.getunits()[2].target)


if __name__ == '__main__':
    for test in [TestTerminologyPlaceable()]:
        for method in dir(test):
            if method.startswith('test_') and callable(getattr(test, method)):
                if hasattr(test, 'setup_method'):
                    getattr(test, 'setup_method')(getattr(test, method))
                getattr(test, method)()
