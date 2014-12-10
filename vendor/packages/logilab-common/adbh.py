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
"""Helpers for DBMS specific (advanced or non standard) functionalities.
"""
__docformat__ = "restructuredtext en"

from warnings import warn
warn('this module is deprecated, use logilab.database instead',
     DeprecationWarning, stacklevel=1)

from logilab.database import (FunctionDescr, get_db_helper as get_adv_func_helper,
                        _GenericAdvFuncHelper,
                        _ADV_FUNC_HELPER_DIRECTORY as ADV_FUNC_HELPER_DIRECTORY)
from logilab.common.decorators import monkeypatch

@monkeypatch(_GenericAdvFuncHelper, 'func_sqlname')
@classmethod
def func_sqlname(cls, funcname):
    funcdef = cls.function_description(funcname)
    return funcdef.name_mapping.get(cls.backend_name, funcname)
