import os
import sys

extra = {}
if sys.version_info >= (3, 0):
    extra.update(use_2to3=True)

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

# -*- Distribution Meta -*-
import re
re_meta = re.compile(r'__(\w+?)__\s*=\s*(.*)')
re_vers = re.compile(r'VERSION\s*=\s*\((.*?)\)')
re_doc = re.compile(r'^"""(.+?)"""', re.M|re.S)
rq = lambda s: s.strip("\"'")

def add_default(m):
    attr_name, attr_value = m.groups()
    return ((attr_name, rq(attr_value)), )


def add_version(m):
    v = list(map(rq, m.groups()[0].split(", ")))
    return (("VERSION", ".".join(v[0:3]) + "".join(v[3:])), )


def add_doc(m):
    return (("doc", m.groups()[0].replace("\n", " ")), )

pats = {re_meta: add_default,
        re_vers: add_version}
here = os.path.abspath(os.path.dirname(__file__))
meta_fh = open(os.path.join(here, "anyjson/__init__.py"))
try:
    meta = {}
    acc = []
    for line in meta_fh:
        if line.strip() == '# -eof meta-':
            break
        acc.append(line)
        for pattern, handler in pats.items():
            m = pattern.match(line.strip())
            if m:
                meta.update(handler(m))
    m = re_doc.match("".join(acc).strip())
    if m:
        meta.update(add_doc(m))
finally:
    meta_fh.close()


supported = ["yajl", "jsonlib2", "jsonlib", "simplejson",
             "json", "django.utils.simplejson", "cjson"]
install_requires = []
for module in supported:
    try:
        __import__(module)
        break
    except ImportError:
        pass
else:
    install_requires.append("simplejson")


setup(name='anyjson',
      version=meta["VERSION"],
      description=meta["doc"],
      author=meta["author"],
      author_email=meta["contact"],
      url=meta["homepage"],
      license='BSD',
      long_description=open("README").read(),
      install_requires=install_requires,
      classifiers=[
            'Development Status :: 5 - Production/Stable',
            'License :: OSI Approved :: BSD License',
            'Operating System :: OS Independent',
            'Intended Audience :: Developers',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.4',
            'Programming Language :: Python :: 2.5',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.1',
            'Programming Language :: Python :: Implementation :: CPython',
            'Programming Language :: Python :: Implementation :: PyPy',
            'Programming Language :: Python :: Implementation :: Jython',
          ],
      keywords='json',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      platforms=["any"],
      test_suite = 'nose.collector',
      **extra
)
