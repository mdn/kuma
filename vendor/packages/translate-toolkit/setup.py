#!/usr/bin/env python

from distutils.core import setup, Extension, Distribution, Command
import distutils.sysconfig
import sys
import os
import os.path
from translate import __version__
from translate import __doc__
try:
  import py2exe
  build_exe = py2exe.build_exe.py2exe
  Distribution = py2exe.Distribution
except ImportError:
  py2exe = None
  build_exe = Command

# TODO: check out installing into a different path with --prefix/--home

join = os.path.join

PRETTY_NAME = 'Translate Toolkit'
translateversion = __version__.sver

packagesdir = distutils.sysconfig.get_python_lib()
sitepackages = packagesdir.replace(sys.prefix + os.sep, '')

infofiles = [(join(sitepackages,'translate'),
             [join('translate',filename) for filename in 'ChangeLog', 'COPYING', 'LICENSE', 'README'])]
initfiles = [(join(sitepackages,'translate'),[join('translate','__init__.py')])]

subpackages = [
        "convert",
        "filters",
        "lang",
        "misc",
        join("misc", "typecheck"),
        "storage",
        join("storage", "placeables"),
        join("storage", "versioncontrol"),
        join("storage", "xml_extract"),
        "search",
        join("search", "indexing"),
        "services",
        "tools",
        ]
# TODO: elementtree doesn't work in sdist, fix this
packages = ["translate"]

translatescripts = [apply(join, ('translate', ) + script) for script in
                  ('convert', 'pot2po'),
                  ('convert', 'moz2po'), ('convert', 'po2moz'),
                  ('convert', 'oo2po'),  ('convert', 'po2oo'),
                  ('convert', 'oo2xliff'),  ('convert', 'xliff2oo'),
                  ('convert', 'prop2po'), ('convert', 'po2prop'),
                  ('convert', 'csv2po'), ('convert', 'po2csv'),
                  ('convert', 'txt2po'), ('convert', 'po2txt'),
                  ('convert', 'ts2po'),  ('convert', 'po2ts'),
                  ('convert', 'html2po'), ('convert', 'po2html'),
                  ('convert', 'ical2po'), ('convert', 'po2ical'),
                  ('convert', 'ini2po'), ('convert', 'po2ini'),
                  ('convert', 'tiki2po'), ('convert', 'po2tiki'),
                  ('convert', 'php2po'), ('convert', 'po2php'),
                  ('convert', 'rc2po'), ('convert', 'po2rc'),
                  ('convert', 'xliff2po'), ('convert', 'po2xliff'),
                  ('convert', 'sub2po'), ('convert', 'po2sub'),
                  ('convert', 'symb2po'), ('convert', 'po2symb'),
                  ('convert', 'po2tmx'),
                  ('convert', 'po2wordfast'),
                  ('convert', 'csv2tbx'),
                  ('convert', 'odf2xliff'), ('convert', 'xliff2odf'),
                  ('convert', 'web2py2po'), ('convert', 'po2web2py'),
                  ('filters', 'pofilter'),
                  ('tools', 'pocompile'),
                  ('tools', 'poconflicts'),
                  ('tools', 'pocount'),
                  ('tools', 'podebug'),
                  ('tools', 'pogrep'),
                  ('tools', 'pomerge'),
                  ('tools', 'porestructure'),
                  ('tools', 'posegment'),
                  ('tools', 'poswap'),
                  ('tools', 'poclean'),
                  ('tools', 'poterminology'),
                  ('tools', 'pretranslate'),
                  ('services', 'lookupclient.py'),
                  ('services', 'lookupservice'),
                  ('services', 'tmserver'),
                  ('tools', 'build_tmdb')]

translatebashscripts = [apply(join, ('tools', ) + (script, )) for script in [
                  'pomigrate2', 'pocompendium', 
                  'posplit', 'popuretext', 'poreencode', 'pocommentclean'
                  ]]

def addsubpackages(subpackages):
  for subpackage in subpackages:
    initfiles.append((join(sitepackages, 'translate', subpackage),
                      [join('translate', subpackage, '__init__.py')]))
    for infofile in ('README', 'TODO'):
      infopath = join('translate', subpackage, infofile)
      if os.path.exists(infopath):
        infofiles.append((join(sitepackages, 'translate', subpackage), [infopath]))
    packages.append("translate.%s" % subpackage)

class build_exe_map(build_exe):
    """distutils py2exe-based class that builds the exe file(s) but allows mapping data files"""
    def reinitialize_command(self, command, reinit_subcommands=0):
        if command == "install_data":
            install_data = build_exe.reinitialize_command(self, command, reinit_subcommands)
            install_data.data_files = self.remap_data_files(install_data.data_files)
            return install_data
        return build_exe.reinitialize_command(self, command, reinit_subcommands)

    def remap_data_files(self, data_files):
        """maps the given data files to different locations using external map_data_file function"""
        new_data_files = []
        for f in data_files:
            if type(f) in (str, unicode):
                f = map_data_file(f)
            else:
                datadir, files = f
                datadir = map_data_file(datadir)
                if datadir is None:
                  f = None
                else:
                  f = datadir, files
            if f is not None:
              new_data_files.append(f)
        return new_data_files

class InnoScript:
    """class that builds an InnoSetup script"""
    def __init__(self, name, lib_dir, dist_dir, exe_files = [], other_files = [], install_scripts = [], version = "1.0"):
        self.lib_dir = lib_dir
        self.dist_dir = dist_dir
        if not self.dist_dir.endswith(os.sep):
            self.dist_dir += os.sep
        self.name = name
        self.version = version
        self.exe_files = [self.chop(p) for p in exe_files]
        self.other_files = [self.chop(p) for p in other_files]
        self.install_scripts = install_scripts

    def getcompilecommand(self):
        try:
            import _winreg
            compile_key = _winreg.OpenKey(_winreg.HKEY_CLASSES_ROOT, "innosetupscriptfile\\shell\\compile\\command")
            compilecommand = _winreg.QueryValue(compile_key, "")
            compile_key.Close()
        except:
            compilecommand = 'compil32.exe "%1"'
        return compilecommand

    def chop(self, pathname):
        """returns the path relative to self.dist_dir"""
        assert pathname.startswith(self.dist_dir)
        return pathname[len(self.dist_dir):]

    def create(self, pathname=None):
        """creates the InnoSetup script"""
        if pathname is None:
          self.pathname = os.path.join(self.dist_dir, self.name + os.extsep + "iss").replace(' ', '_')
        else:
          self.pathname = pathname
# See http://www.jrsoftware.org/isfaq.php for more InnoSetup config options.
        ofi = self.file = open(self.pathname, "w")
        print >> ofi, "; WARNING: This script has been created by py2exe. Changes to this script"
        print >> ofi, "; will be overwritten the next time py2exe is run!"
        print >> ofi, r"[Setup]"
        print >> ofi, r"AppName=%s" % self.name
        print >> ofi, r"AppVerName=%s %s" % (self.name, self.version)
        print >> ofi, r"DefaultDirName={pf}\%s" % self.name
        print >> ofi, r"DefaultGroupName=%s" % self.name
        print >> ofi, r"OutputBaseFilename=%s-%s-setup" % (self.name, self.version)
        print >> ofi, r"ChangesEnvironment=yes"
        print >> ofi
        print >> ofi, r"[Files]"
        for path in self.exe_files + self.other_files:
            print >> ofi, r'Source: "%s"; DestDir: "{app}\%s"; Flags: ignoreversion' % (path, os.path.dirname(path))
        print >> ofi
        print >> ofi, r"[Icons]"
        print >> ofi, r'Name: "{group}\Documentation"; Filename: "{app}\doc\index.html";'
        print >> ofi, r'Name: "{group}\Translate Toolkit Command Prompt"; Filename: "cmd.exe"'
        print >> ofi, r'Name: "{group}\Uninstall %s"; Filename: "{uninstallexe}"' % self.name
        print >> ofi
        print >> ofi, r"[Registry]"
        # TODO: Move the code to update the Path environment variable to a Python script which will be invoked by the [Run] section (below)
        print >> ofi, r'Root: HKCU; Subkey: "Environment"; ValueType: expandsz; ValueName: "Path"; ValueData: "{reg:HKCU\Environment,Path|};{app};"'
        print >> ofi        
        if self.install_scripts:
            print >> ofi, r"[Run]"
            for path in self.install_scripts:
                print >> ofi, r'Filename: "{app}\%s"; WorkingDir: "{app}"; Parameters: "-install"' % path
            print >> ofi
            print >> ofi, r"[UninstallRun]"
            for path in self.install_scripts:
                print >> ofi, r'Filename: "{app}\%s"; WorkingDir: "{app}"; Parameters: "-remove"' % path
        print >> ofi
        ofi.close()

    def compile(self):
        """compiles the script using InnoSetup"""
        shellcompilecommand = self.getcompilecommand()
        compilecommand = shellcompilecommand.replace('"%1"', self.pathname)
        result = os.system(compilecommand)
        if result:
            print "Error compiling iss file"
            print "Opening iss file, use InnoSetup GUI to compile manually"
            os.startfile(self.pathname)

class build_installer(build_exe_map):
    """distutils class that first builds the exe file(s), then creates a Windows installer using InnoSetup"""
    description = "create an executable installer for MS Windows using InnoSetup and py2exe"
    user_options = getattr(build_exe, 'user_options', []) + \
        [('install-script=', None,
          "basename of installation script to be run after installation or before deinstallation")]

    def initialize_options(self):
        build_exe.initialize_options(self)
        self.install_script = None

    def run(self):
        # First, let py2exe do it's work.
        build_exe.run(self)
        lib_dir = self.lib_dir
        dist_dir = self.dist_dir
        # create the Installer, using the files py2exe has created.
        exe_files = self.windows_exe_files + self.console_exe_files
        install_scripts = self.install_script
        if isinstance(install_scripts, (str, unicode)):
            install_scripts = [install_scripts]
        script = InnoScript(PRETTY_NAME, lib_dir, dist_dir, exe_files, self.lib_files, version=self.distribution.metadata.version, install_scripts=install_scripts)
        print "*** creating the inno setup script***"
        script.create()
        print "*** compiling the inno setup script***"
        script.compile()
        # Note: By default the final setup.exe will be in an Output subdirectory.

def import_setup_module(modulename, modulepath):
  import imp
  modfile, pathname, description = imp.find_module(modulename, [modulepath])
  return imp.load_module(modulename, modfile, pathname, description)

def map_data_file (data_file):
  """remaps a data_file (could be a directory) to a different location
  This version gets rid of Lib\\site-packages, etc"""
  data_parts = data_file.split(os.sep)
  if data_parts[:2] == ["Lib", "site-packages"]:
    data_parts = data_parts[2:]
    if data_parts:
      data_file = os.path.join(*data_parts)
    else:
      data_file = ""
  if data_parts[:1] == ["translate"]:
    data_parts = data_parts[1:]
    if data_parts:
      data_file = os.path.join(*data_parts)
    else:
      data_file = ""
  return data_file

def getdatafiles():
  datafiles = initfiles + infofiles
  def listfiles(srcdir):
    return join(sitepackages, srcdir), [join(srcdir, f) for f in os.listdir(srcdir) if os.path.isfile(join(srcdir, f))]
  docfiles = []
  for subdir in ['doc', 'share']:
    docwalk=os.walk(os.path.join('translate', subdir))
    for docs in docwalk:
      if not '.svn' in docs[0]:
        docfiles.append(listfiles(docs[0]))
    datafiles += docfiles
  return datafiles

def buildinfolinks():
  linkfile = getattr(os, 'symlink', None)
  linkdir = getattr(os, 'symlink', None)
  import shutil
  if linkfile is None:
    linkfile = shutil.copy2
  if linkdir is None:
    linkdir = shutil.copytree
  basedir = os.path.abspath(os.curdir)
  os.chdir("translate")
  if os.path.exists("LICENSE") or os.path.islink("LICENSE"):
    os.remove("LICENSE")
  linkfile("COPYING", "LICENSE")
  os.chdir(basedir)
  for infofile in ["COPYING", "README", "LICENSE"]:
    if os.path.exists(infofile) or os.path.islink(infofile):
      os.remove(infofile)
    linkfile(os.path.join("translate", infofile), infofile)

def buildmanifest_in(file, scripts):
  """This writes the required files to a MANIFEST.in file"""
  print >>file, "# MANIFEST.in: the below autogenerated by setup.py from translate %s" % translateversion
  print >>file, "# things needed by translate setup.py to rebuild"
  print >>file, "# informational files"
  for infofile in ("README", "TODO", "ChangeLog", "COPYING", "LICENSE", "*.txt"):
    print >>file, "global-include %s" % infofile
  print >>file, "# C programs"
  print >>file, "global-include *.c"
  print >> file, "# scripts which don't get included by default in sdist"
  for scriptname in scripts:
    print >>file, "include %s" % scriptname
  print >> file, "# include our documentation"
  print >> file, "graft translate/doc"
  print >> file, "graft translate/share"
  # wordlist, portal are in the source tree but unconnected to the python code
  print >>file, "prune wordlist"
  print >>file, "prune spelling"
  print >>file, "prune lingua"
  print >>file, "prune Pootle"
  print >>file, "prune pootling"
  print >>file, "prune virtaal"
  print >>file, "prune spelt"
  print >>file, "prune corpuscatcher"
  print >>file, "prune .svn"
  print >>file, "# MANIFEST.in: the above autogenerated by setup.py from translate %s" % translateversion

class TranslateDistribution(Distribution):
  """a modified distribution class for translate"""
  def __init__(self, attrs):
    baseattrs = {}
    py2exeoptions = {}
    py2exeoptions["packages"] = ["translate", "encodings"]
    py2exeoptions["compressed"] = True
    py2exeoptions["excludes"] = ["PyLucene", "Tkconstants", "Tkinter", "tcl"]
    version = attrs.get("version", translateversion)
    py2exeoptions["dist_dir"] = "translate-toolkit-%s" % version
    py2exeoptions["includes"] = ["lxml", "lxml._elementpath", "psyco"]
    options = {"py2exe": py2exeoptions}
    baseattrs['options'] = options
    if py2exe:
      baseattrs['console'] = translatescripts
      baseattrs['zipfile'] = "translate.zip"
      baseattrs['cmdclass'] = {"py2exe": build_exe_map, "innosetup": build_installer}
      options["innosetup"] = py2exeoptions.copy()
      options["innosetup"]["install_script"] = []
    baseattrs.update(attrs)
    Distribution.__init__(self, baseattrs)

def standardsetup(name, version, custompackages=[], customdatafiles=[]):
  buildinfolinks()
  # TODO: make these end with .py ending on Windows...
  try:
    manifest_in = open("MANIFEST.in", "w")
    buildmanifest_in(manifest_in, translatescripts + translatebashscripts)
    manifest_in.close()
  except IOError, e:
    print >> sys.stderr, "warning: could not recreate MANIFEST.in, continuing anyway. Error was %s" % e
  addsubpackages(subpackages)
  datafiles = getdatafiles()
  ext_modules = []
  dosetup(name, version, packages + custompackages, datafiles + customdatafiles, translatescripts+ translatebashscripts, ext_modules)

classifiers = [
  "Development Status :: 5 - Production/Stable",
  "Environment :: Console",
  "Intended Audience :: Developers",
  "License :: OSI Approved :: GNU General Public License (GPL)",
  "Programming Language :: Python",
  "Topic :: Software Development :: Localization",
  "Topic :: Software Development :: Libraries :: Python Modules",
  "Operating System :: OS Independent",
  "Operating System :: Microsoft :: Windows",
  "Operating System :: Unix"
  ]

def dosetup(name, version, packages, datafiles, scripts, ext_modules=[]):
  long_description = __doc__
  description = __doc__.split("\n", 1)[0]
  setup(name=name,
        version=version,
        license="GNU General Public License (GPL)",
        description=description,
        long_description=long_description,
        author="Translate.org.za",
        author_email="translate-devel@lists.sourceforge.net",
        url="http://translate.sourceforge.net/wiki/toolkit/index",
        download_url="http://sourceforge.net/project/showfiles.php?group_id=91920&package_id=97082",
        platforms=["any"],
        classifiers=classifiers,
        packages=packages,
        data_files=datafiles,
        scripts=scripts,
        ext_modules=ext_modules,
        distclass=TranslateDistribution
        )

if __name__ == "__main__":
  standardsetup("translate-toolkit", translateversion)

