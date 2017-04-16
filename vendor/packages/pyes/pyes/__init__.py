#!/usr/bin/python
# -*- coding: utf-8 -*-

import logging
logger = logging.getLogger(__name__)

VERSION = (0, 16, 0)

__version__ = ".".join(map(str, VERSION[0:3])) + "".join(VERSION[3:])
__author__ = "Alberto Paro"
__contact__ = "alberto.paro@gmail.com"
__homepage__ = "http://github.com/aparo/pyes/"
__docformat__ = "restructuredtext"


def is_stable_release():
    if len(VERSION) > 3 and isinstance(VERSION[3], basestring):
        return False
    return not VERSION[1] % 2


def version_with_meta():
    return "%s (%s)" % (__version__,
                        is_stable_release() and "stable" or "unstable")

from es import ES, file_to_attachment, decode_json
from query import *
from rivers import *
from filters import *
#from highlight import HighLighter
from utils import *
try:
    #useful for additional query extra features
    from query_extra import *
except ImportError:
    pass

try:
    #useful for additional features for django users
    from djangoutils import *
except ImportError:
    pass
