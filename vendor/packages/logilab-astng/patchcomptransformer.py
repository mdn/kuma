# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU Lesser General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
# copyright 2003-2010 LOGILAB S.A. (Paris, FRANCE), all rights reserved.
# contact http://www.logilab.fr/ -- mailto:contact@logilab.fr
# copyright 2003-2010 Sylvain Thenault, all rights reserved.
# contact mailto:thenault@gmail.com
#
# This file is part of logilab-astng.
#
# logilab-astng is free software: you can redistribute it and/or modify it
# under the terms of the GNU Lesser General Public License as published by the
# Free Software Foundation, either version 2.1 of the License, or (at your
# option) any later version.
#
# logilab-astng is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or
# FITNESS FOR A PARTICULAR PURPOSE.  See the GNU Lesser General Public License
# for more details.
#
# You should have received a copy of the GNU Lesser General Public License along
# with logilab-astng. If not, see <http://www.gnu.org/licenses/>.
"""Monkey patch compiler.transformer to fix line numbering bugs

"""
# TODO : move this module to _nodes_compiler

from types import TupleType
from token import DEDENT
from compiler import transformer

import compiler.ast as nodes

def fromto_lineno(asttuple):
    """return the minimum and maximum line number of the given ast tuple"""
    return from_lineno(asttuple), to_lineno(asttuple)

def from_lineno(asttuple):
    """return the minimum line number of the given ast tuple"""
    while type(asttuple[1]) is TupleType:
        asttuple = asttuple[1]
    return asttuple[2]

def to_lineno(asttuple):
    """return the maximum line number of the given ast tuple"""
    while type(asttuple[1]) is TupleType:
        for i in xrange(len(asttuple) - 1, 0, -1):
            if asttuple[i][0] != DEDENT:
                asttuple = asttuple[i]
                break
        else:
            raise Exception()
    return asttuple[2]

def fix_lineno(node, fromast, toast=None, blockast=None):
    if getattr(node, 'fromlineno', None) is not None:
        return node
    if isinstance(node, nodes.Stmt):
        return node
    if toast is None or toast is fromast:
        node.fromlineno, node.tolineno = fromto_lineno(fromast)
    else:
        node.fromlineno, node.tolineno = from_lineno(fromast), to_lineno(toast)
    if blockast:
        node.blockstart_tolineno = to_lineno(blockast)
    return node

BaseTransformer = transformer.Transformer

COORD_MAP = {
    # if: test ':' suite ('elif' test ':' suite)* ['else' ':' suite]
    'if': 0,
    # 'while' test ':' suite ['else' ':' suite]
    'while': 1,
    # 'for' exprlist 'in' exprlist ':' suite ['else' ':' suite]
    'for': 3,
    # 'try' ':' suite (except_clause ':' suite)+ ['else' ':' suite]
    'try': 0,
    # | 'try' ':' suite 'finally' ':' suite
    # XXX with
    }

def fixlineno_wrap(function, stype):
    def fixlineno_wrapper(self, nodelist):
        node = function(self, nodelist)
        try:
            blockstart_idx = COORD_MAP[stype]
        except KeyError:
            return fix_lineno(node, nodelist[0], nodelist[-1])
        else:
            return fix_lineno(node, nodelist[0], nodelist[-1], nodelist[blockstart_idx])
    return fixlineno_wrapper

class ASTNGTransformer(BaseTransformer):
    """overrides transformer for a better source line number handling"""
    def com_NEWLINE(self, *args):
        # A ';' at the end of a line can make a NEWLINE token appear
        # here, Render it harmless. (genc discards ('discard',
        # ('const', xxxx)) Nodes)
        lineno = args[0][1]
        # don't put fromlineno/tolineno on Const None to mark it as dynamically
        # added, without "physical" reference in the source
        n = nodes.Discard(nodes.Const(None))
        n.fromlineno = n.tolineno = lineno
        return n
    
    def com_node(self, node):
        res = self._dispatch[node[0]](node[1:])
        return fix_lineno(res, node)
    
    def com_assign(self, node, assigning):
        res = BaseTransformer.com_assign(self, node, assigning)
        return fix_lineno(res, node)
    
    def com_apply_trailer(self, primaryNode, nodelist):
        node = BaseTransformer.com_apply_trailer(self, primaryNode, nodelist)
        return fix_lineno(node, nodelist)
    
    def funcdef(self, nodelist):
        node = BaseTransformer.funcdef(self, nodelist)
        if node.decorators is not None:
            fix_lineno(node.decorators, nodelist[0])
        return fix_lineno(node, nodelist[-5], nodelist[-1], nodelist[-3])
    
    def lambdef(self, nodelist):
        node = BaseTransformer.lambdef(self, nodelist)
        return fix_lineno(node, nodelist[1], nodelist[-1])
    
    def classdef(self, nodelist):
        node = BaseTransformer.classdef(self, nodelist)
        return fix_lineno(node, nodelist[0], nodelist[-1], nodelist[-2])

    def file_input(self, nodelist):
        node = BaseTransformer.file_input(self, nodelist)
        if node.node.nodes:
            node.tolineno = node.node.nodes[-1].tolineno
        else:
            node.tolineno = 0
        return node
    
# wrap *_stmt methods
for name in dir(BaseTransformer):
    if name.endswith('_stmt') and not (name in ('com_stmt',
                                                'com_append_stmt')
                                       or name in ASTNGTransformer.__dict__):
        setattr(BaseTransformer, name,
                fixlineno_wrap(getattr(BaseTransformer, name), name[:-5]))
            
transformer.Transformer = ASTNGTransformer

