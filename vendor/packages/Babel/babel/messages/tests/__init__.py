# -*- coding: utf-8 -*-
#
# Copyright (C) 2007 Edgewall Software
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://babel.edgewall.org/wiki/License.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://babel.edgewall.org/log/.

import unittest

def suite():
    from babel.messages.tests import catalog, extract, frontend, mofile, \
                                     plurals, pofile, checkers
    suite = unittest.TestSuite()
    suite.addTest(catalog.suite())
    suite.addTest(extract.suite())
    suite.addTest(frontend.suite())
    suite.addTest(mofile.suite())
    suite.addTest(pofile.suite())
    suite.addTest(checkers.suite())
    return suite

if __name__ == '__main__':
    unittest.main(defaultTest='suite')
