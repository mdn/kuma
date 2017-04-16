# encoding: iso-8859-15
# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
#
# This file is part of logilab-common.
#
# logilab-common is free software: you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free
# Software Foundation, either version 2.1 of the License, or (at your option) any
# later version.
#
# logilab-common is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License for more
# details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-common.  If not, see <http://www.gnu.org/licenses/>.

from logilab.common.testlib import TestCase, unittest_main
from logilab.common.umessage import UMessage, decode_QP

import email

class UMessageTC(TestCase):

    def setUp(self):
        msg1 = email.message_from_file(open('data/test1.msg'))
        self.umessage1 = UMessage(msg1)
        msg2 = email.message_from_file(open('data/test2.msg'))
        self.umessage2 = UMessage(msg2)

    def test_get_subject(self):
        subj = self.umessage2.get('Subject')
        self.assertEquals(type(subj), unicode)
        self.assertEquals(subj, u'� LA MER')

    def test_get_all(self):
        to = self.umessage2.get_all('To')
        self.assertEquals(type(to[0]), unicode)
        self.assertEquals(to, [u'�l�ment � accents <alf@logilab.fr>'])

    def test_get_payload_no_multi(self):
        payload = self.umessage1.get_payload()
        self.assertEquals(type(payload), unicode)

    def test_decode_QP(self):
        test_line =  '=??b?UmFwaGHrbA==?= DUPONT<raphael.dupont@societe.fr>'
        test = decode_QP(test_line)
        self.assertEquals(type(test), unicode)
        self.assertEquals(test, u'Rapha�l DUPONT<raphael.dupont@societe.fr>')


if __name__ == '__main__':
    unittest_main()
