#pylint: disable-msg=W0401,W0611
"""check unexistant names imported are reported"""

__revision__ = None

import logilab.common.tutu
from logilab.common import toto
toto.yo()

from logilab.common import modutils
modutils.nonexistant_function()
modutils.another.nonexistant.function()
print logilab.common.modutils.yo

import sys
print >> sys.stdout, 'hello world'
print >> sys.stdoout, 'bye bye world'


import re
re.finditer('*', 'yo')

from rie import *
from re import findiiter, compiile

import os
os.environ.has_key('SOMEVAR')

import exceptions
print exceptions.__dict__
print exceptions.__dict__.get('Exception')
