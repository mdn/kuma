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
"""astng manager: avoid multiple astng build of a same module when
possible by providing a class responsible to get astng representation
from various source and using a cache of built modules)

"""

__docformat__ = "restructuredtext en"

import sys
import os
from os.path import dirname, basename, abspath, join, isdir, exists

from logilab.common.modutils import NoSourceFile, is_python_source, \
     file_from_modpath, load_module_from_name, modpath_from_file, \
     get_module_files, get_source_file, zipimport
from logilab.common.configuration import OptionsProviderMixIn

from logilab.astng._exceptions import ASTNGBuildingException

def astng_wrapper(func, modname):
    """wrapper to give to ASTNGManager.project_from_files"""
    print 'parsing %s...' % modname
    try:
        return func(modname)
    except ASTNGBuildingException, exc:
        print exc
    except KeyboardInterrupt:
        raise
    except Exception, exc:
        import traceback
        traceback.print_exc()

def safe_repr(obj):
    try:
        return repr(obj)
    except:
        return '???'

def zip_import_data(filepath):
    if zipimport is None:
        return None, None
    for ext in ('.zip', '.egg'):
        try:
            eggpath, resource = filepath.split(ext + '/', 1)
        except ValueError:
            continue
        try:
            importer = zipimport.zipimporter(eggpath + ext)
            return importer.get_source(resource), resource.replace('/', '.')
        except:
            continue
    return None, None


class ASTNGManager(OptionsProviderMixIn):
    """the astng manager, responsible to build astng from files
     or modules.

    Use the Borg pattern.
    """

    name = 'astng loader'
    options = (("ignore",
                {'type' : "csv", 'metavar' : "<file>",
                 'dest' : "black_list", "default" : ('CVS',),
                 'help' : "add <file> (may be a directory) to the black list\
. It should be a base name, not a path. You may set this option multiple times\
."}),
               ("project",
                {'default': "No Name", 'type' : 'string', 'short': 'p',
                 'metavar' : '<project name>',
                 'help' : 'set the project name.'}),
               )
    brain = {}
    def __init__(self, borg=True):
        if borg:
            self.__dict__ = ASTNGManager.brain
        if not self.__dict__:
            OptionsProviderMixIn.__init__(self)
            self.load_defaults()
            # NOTE: cache entries are added by the [re]builder
            self._cache = {} #Cache(cache_size)
            self._mod_file_cache = {}

    def reset_cache(self):
        self._cache = {} #Cache(cache_size)
        self._mod_file_cache = {}

    def from_directory(self, directory, modname=None):
        """given a module name, return the astng object"""
        modname = modname or basename(directory)
        directory = abspath(directory)
        return Package(directory, modname, self)

    def astng_from_file(self, filepath, modname=None, fallback=True):
        """given a module name, return the astng object"""
        try:
            filepath = get_source_file(filepath, include_no_ext=True)
            source = True
        except NoSourceFile:
            source = False
        if modname is None:
            modname = '.'.join(modpath_from_file(filepath))
        if modname in self._cache:
            return self._cache[modname]
        if source:
            try:
                from logilab.astng.builder import ASTNGBuilder
                return ASTNGBuilder(self).file_build(filepath, modname)
            except (SyntaxError, KeyboardInterrupt, SystemExit):
                raise
            except Exception, ex:
                raise
                if __debug__:
                    print 'error while building astng for', filepath
                    import traceback
                    traceback.print_exc()
                msg = 'Unable to load module %s (%s)' % (modname, ex)
                raise ASTNGBuildingException(msg), None, sys.exc_info()[-1]
        elif fallback and modname:
            return self.astng_from_module_name(modname)
        raise ASTNGBuildingException('unable to get astng for file %s' %
                                     filepath)

    def astng_from_module_name(self, modname, context_file=None):
        """given a module name, return the astng object"""
        if modname in self._cache:
            return self._cache[modname]
        old_cwd = os.getcwd()
        if context_file:
            os.chdir(dirname(context_file))
        try:
            filepath = self.file_from_module_name(modname, context_file)
            if filepath is not None and not is_python_source(filepath):
                data, zmodname = zip_import_data(filepath)
                if data is not None:
                    from logilab.astng.builder import ASTNGBuilder
                    try:
                        return ASTNGBuilder(self).string_build(data, zmodname,
                                                               filepath)
                    except (SyntaxError, KeyboardInterrupt, SystemExit):
                        raise
            if filepath is None or not is_python_source(filepath):
                try:
                    module = load_module_from_name(modname)
                # catch SystemError as well, we may get that on badly
                # initialized C-module
                except (SystemError, ImportError), ex:
                    msg = 'Unable to load module %s (%s)' % (modname, ex)
                    raise ASTNGBuildingException(msg)
                return self.astng_from_module(module, modname)
            return self.astng_from_file(filepath, modname, fallback=False)
        finally:
            os.chdir(old_cwd)

    def file_from_module_name(self, modname, contextfile):
        try:
            value = self._mod_file_cache[(modname, contextfile)]
        except KeyError:
            try:
                value = file_from_modpath(modname.split('.'),
                                          context_file=contextfile)
            except ImportError, ex:
                msg = 'Unable to load module %s (%s)' % (modname, ex)
                value = ASTNGBuildingException(msg)
            self._mod_file_cache[(modname, contextfile)] = value
        if isinstance(value, ASTNGBuildingException):
            raise value
        return value

    def astng_from_module(self, module, modname=None):
        """given an imported module, return the astng object"""
        modname = modname or module.__name__
        if modname in self._cache:
            return self._cache[modname]
        try:
            # some builtin modules don't have __file__ attribute
            filepath = module.__file__
            if is_python_source(filepath):
                return self.astng_from_file(filepath, modname)
        except AttributeError:
            pass
        from logilab.astng.builder import ASTNGBuilder
        return ASTNGBuilder(self).module_build(module, modname)

    def astng_from_class(self, klass, modname=None):
        """get astng for the given class"""
        if modname is None:
            try:
                modname = klass.__module__
            except AttributeError:
                raise ASTNGBuildingException(
                    'Unable to get module for class %s' % safe_repr(klass))
        modastng = self.astng_from_module_name(modname)
        return modastng.getattr(klass.__name__)[0] # XXX


    def infer_astng_from_something(self, obj, modname=None, context=None):
        """infer astng for the given class"""
        if hasattr(obj, '__class__') and not isinstance(obj, type):
            klass = obj.__class__
        else:
            klass = obj
        if modname is None:
            try:
                modname = klass.__module__
            except AttributeError:
                raise ASTNGBuildingException(
                    'Unable to get module for %s' % safe_repr(klass))
            except Exception, ex:
                raise ASTNGBuildingException(
                    'Unexpected error while retrieving module for %s: %s'
                    % (safe_repr(klass), ex))
        try:
            name = klass.__name__
        except AttributeError:
            raise ASTNGBuildingException(
                'Unable to get name for %s' % safe_repr(klass))
        except Exception, ex:
            raise ASTNGBuildingException(
                'Unexpected error while retrieving name for %s: %s'
                % (safe_repr(klass), ex))
        # take care, on living object __module__ is regularly wrong :(
        modastng = self.astng_from_module_name(modname)
        if klass is obj:
            for  infered in modastng.igetattr(name, context):
                yield infered
        else:
            for infered in modastng.igetattr(name, context):
                yield infered.instanciate_class()

    def project_from_files(self, files, func_wrapper=astng_wrapper,
                           project_name=None, black_list=None):
        """return a Project from a list of files or modules"""
        # insert current working directory to the python path to have a correct
        # behaviour
        sys.path.insert(0, os.getcwd())
        try:
            # build the project representation
            project_name = project_name or self.config.project
            black_list = black_list or self.config.black_list
            project = Project(project_name)
            for something in files:
                if not exists(something):
                    fpath = file_from_modpath(something.split('.'))
                elif isdir(something):
                    fpath = join(something, '__init__.py')
                else:
                    fpath = something
                astng = func_wrapper(self.astng_from_file, fpath)
                if astng is None:
                    continue
                project.path = project.path or astng.file
                project.add_module(astng)
                base_name = astng.name
                # recurse in package except if __init__ was explicitly given
                if astng.package and something.find('__init__') == -1:
                    # recurse on others packages / modules if this is a package
                    for fpath in get_module_files(dirname(astng.file),
                                                  black_list):
                        astng = func_wrapper(self.astng_from_file, fpath)
                        if astng is None or astng.name == base_name:
                            continue
                        project.add_module(astng)
            return project
        finally:
            sys.path.pop(0)



class Package:
    """a package using a dictionary like interface

    load submodules lazily, as they are needed
    """

    def __init__(self, path, name, manager):
        self.name = name
        self.path = abspath(path)
        self.manager = manager
        self.parent = None
        self.lineno = 0
        self.__keys = None
        self.__subobjects = None

    def fullname(self):
        """return the full name of the package (i.e. prefix by the full name
        of the parent package if any
        """
        if self.parent is None:
            return self.name
        return '%s.%s' % (self.parent.fullname(), self.name)

    def get_subobject(self, name):
        """method used to get sub-objects lazily : sub package or module are
        only build once they are requested
        """
        if self.__subobjects is None:
            try:
                self.__subobjects = dict.fromkeys(self.keys())
            except AttributeError:
                # python <= 2.3
                self.__subobjects = dict([(k, None) for k in self.keys()])
        obj = self.__subobjects[name]
        if obj is None:
            objpath = join(self.path, name)
            if isdir(objpath):
                obj = Package(objpath, name, self.manager)
                obj.parent = self
            else:
                modname = '%s.%s' % (self.fullname(), name)
                obj = self.manager.astng_from_file(objpath + '.py', modname)
            self.__subobjects[name] = obj
        return obj

    def get_module(self, modname):
        """return the Module or Package object with the given name if any
        """
        path = modname.split('.')
        if path[0] != self.name:
            raise KeyError(modname)
        obj = self
        for part in path[1:]:
            obj = obj.get_subobject(part)
        return obj

    def keys(self):
        if self.__keys is None:
            self.__keys = []
            for fname in os.listdir(self.path):
                if fname.endswith('.py'):
                    self.__keys.append(fname[:-3])
                    continue
                fpath = join(self.path, fname)
                if isdir(fpath) and exists(join(fpath, '__init__.py')):
                    self.__keys.append(fname)
            self.__keys.sort()
        return self.__keys[:]

    def values(self):
        return [self.get_subobject(name) for name in self.keys()]

    def items(self):
        return zip(self.keys(), self.values())

    def has_key(self, name):
        return bool(self.get(name))

    def get(self, name, default=None):
        try:
            return self.get_subobject(name)
        except KeyError:
            return default

    def __getitem__(self, name):
        return self.get_subobject(name)
    def __contains__(self, name):
        return self.has_key(name)
    def __iter__(self):
        return iter(self.keys())


class Project:
    """a project handle a set of modules / packages"""
    def __init__(self, name=''):
        self.name = name
        self.path = None
        self.modules = []
        self.locals = {}
        self.__getitem__ = self.locals.__getitem__
        self.__iter__ = self.locals.__iter__
        self.values = self.locals.values
        self.keys = self.locals.keys
        self.items = self.locals.items
        self.has_key = self.locals.has_key

    def add_module(self, node):
        self.locals[node.name] = node
        self.modules.append(node)

    def get_module(self, name):
        return self.locals[name]

    def get_children(self):
        return self.modules

    def __repr__(self):
        return '<Project %r at %s (%s modules)>' % (self.name, id(self),
                                                    len(self.modules))

