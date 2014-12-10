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
"""The ASTNGBuilder makes astng from living object and / or from compiler.ast

With python >= 2.5, the internal _ast module is used instead

The builder is not thread safe and can't be used to parse different sources
at the same time.


"""

__docformat__ = "restructuredtext en"

import sys
from os.path import splitext, basename, dirname, exists, abspath
from inspect import isfunction, ismethod, ismethoddescriptor, isclass, \
     isbuiltin
from inspect import isdatadescriptor

from logilab.common.fileutils import norm_read
from logilab.common.modutils import modpath_from_file

from logilab.astng._exceptions import ASTNGBuildingException
from logilab.astng.raw_building import *

try:
    from _ast import PyCF_ONLY_AST
    def parse(string):
        return compile(string, "<string>", 'exec', PyCF_ONLY_AST)
    from logilab.astng._nodes_ast import TreeRebuilder
except ImportError, exc:
    from compiler import parse
    from logilab.astng import patchcomptransformer
    from logilab.astng._nodes_compiler import TreeRebuilder

# ast NG builder ##############################################################

class ASTNGBuilder:
    """provide astng building methods
    """

    def __init__(self, manager=None):
        if manager is None:
            from logilab.astng import MANAGER as manager
        self._manager = manager
        self._module = None
        self._file = None
        self._done = None
        self.rebuilder = TreeRebuilder(manager)
        self._dyn_modname_map = {'gtk': 'gtk._gtk'}

    def module_build(self, module, modname=None):
        """build an astng from a living module instance
        """
        node = None
        self._module = module
        path = getattr(module, '__file__', None)
        if path is not None:
            path_, ext = splitext(module.__file__)
            if ext in ('.py', '.pyc', '.pyo') and exists(path_ + '.py'):
                node = self.file_build(path_ + '.py', modname)
        if node is None:
            # this is a built-in module
            # get a partial representation by introspection
            node = self.inspect_build(module, modname=modname, path=path)
        return node

    def inspect_build(self, module, modname=None, path=None):
        """build astng from a living module (i.e. using inspect)
        this is used when there is no python source code available (either
        because it's a built-in module or because the .py is not available)
        """
        self._module = module
        if modname is None:
            modname = module.__name__
        node = build_module(modname, module.__doc__)
        node.file = node.path = path and abspath(path) or path
        if self._manager is not None:
            self._manager._cache[modname] = node
        node.package = hasattr(module, '__path__')
        self._done = {}
        self.object_build(node, module)
        return node

    def file_build(self, path, modname=None):
        """build astng from a source code file (i.e. from an ast)

        path is expected to be a python source file
        """
        try:
            data = norm_read(path)
        except IOError, ex:
            msg = 'Unable to load file %r (%s)' % (path, ex)
            raise ASTNGBuildingException(msg)
        self._file = path
        # get module name if necessary, *before modifying sys.path*
        if modname is None:
            try:
                modname = '.'.join(modpath_from_file(path))
            except ImportError:
                modname = splitext(basename(path))[0]
        # build astng representation
        try:
            sys.path.insert(0, dirname(path))
            node = self.string_build(data, modname, path)
            node.file = abspath(path)
        finally:
            self._file = None
            sys.path.pop(0)

        return node

    def string_build(self, data, modname='', path=None):
        """build astng from a source code stream (i.e. from an ast)"""
        return self.ast_build(parse(data + '\n'), modname, path)

    def ast_build(self, node, modname='', path=None):
        """build the astng from AST, return the new tree"""
        if path is not None:
            node_file = abspath(path)
        else:
            node_file = '<?>'
        if modname.endswith('.__init__'):
            modname = modname[:-9]
            package = True
        else:
            package = path and path.find('__init__.py') > -1 or False
        newnode = self.rebuilder.build(node, modname, node_file)
        newnode.package = package
        return newnode

    # astng from living objects ###############################################
    #
    # this is actually a really minimal representation, including only Module,
    # Function and Class nodes and some others as guessed

    def object_build(self, node, obj):
        """recursive method which create a partial ast from real objects
         (only function, class, and method are handled)
        """
        if self._done.has_key(obj):
            return self._done[obj]
        self._done[obj] = node
        for name in dir(obj):
            try:
                member = getattr(obj, name)
            except AttributeError:
                # damned ExtensionClass.Base, I know you're there !
                attach_dummy_node(node, name)
                continue
            if ismethod(member):
                member = member.im_func
            if isfunction(member):
                # verify this is not an imported function
                if member.func_code.co_filename != getattr(self._module, '__file__', None):
                    attach_dummy_node(node, name, member)
                    continue
                object_build_function(node, member, name)
            elif isbuiltin(member):
                # verify this is not an imported member
                if self._member_module(member) != self._module.__name__:
                    imported_member(node, member, name)
                    continue
                object_build_methoddescriptor(node, member, name)
            elif isclass(member):
                # verify this is not an imported class
                if self._member_module(member) != self._module.__name__:
                    imported_member(node, member, name)
                    continue
                if member in self._done:
                    class_node = self._done[member]
                    if not class_node in node.locals.get(name, ()):
                        node.add_local_node(class_node, name)
                else:
                    class_node = object_build_class(node, member, name)
                    # recursion
                    self.object_build(class_node, member)
            elif ismethoddescriptor(member):
                assert isinstance(member, object)
                object_build_methoddescriptor(node, member, name)
            elif isdatadescriptor(member):
                assert isinstance(member, object)
                object_build_datadescriptor(node, member, name)
            elif isinstance(member, (int, long, float, str, unicode)) or member is None:
                attach_const_node(node, name, member)
            else:
                # create an empty node so that the name is actually defined
                attach_dummy_node(node, name, member)

    def _member_module(self, member):
        modname = getattr(member, '__module__', None)
        return self._dyn_modname_map.get(modname, modname)


def imported_member(node, member, name):
    """consider a class/builtin member where __module__ != current module name

    check if it's sound valid and then add an import node, else use a dummy node
    """
    # /!\ some classes like ExtensionClass doesn't have a
    # __module__ attribute !
    member_module = getattr(member, '__module__', '__builtin__')
    try:
        getattr(sys.modules[member_module], name)
    except (KeyError, AttributeError):
        attach_dummy_node(node, name, member)
    else:
        attach_import_node(node, member_module, name)

