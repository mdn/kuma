#!/usr/bin/env python

V = "0.8"

from distutils.core import setup
setup(name='lockfile',
      author='Skip Montanaro',
      author_email='skip@pobox.com',
      url='http://smontanaro.dyndns.org/python/',
      download_url=('http://smontanaro.dyndns.org/python/lockfile-%s.tar.gz' %
                    V),
      version=V,
      description="Platform-independent file locking module",
      long_description="""
The lockfile module exports a FileLock class which provides a simple
API for locking files.  Unlike the Windows msvcrt.locking function,
the Unix fcntl.flock, fcntl.lockf and the deprecated posixfile module,
the API is identical across both Unix (including Linux and Mac) and
Windows platforms.  The lock mechanism relies on the atomic nature of
the link (on Unix) and mkdir (on Windows) system calls.

Version %s fixes several bugs relating to threads and test reorganization.""" % V,
      py_modules=['lockfile'],
      license='MIT License',
      classifiers=[
          'Development Status :: 4 - Beta',
          'Intended Audience :: Developers',
          'License :: OSI Approved :: MIT License',
          'Operating System :: MacOS',
          'Operating System :: Microsoft :: Windows :: Windows NT/2000',
          'Operating System :: POSIX',
          'Programming Language :: Python',
          'Programming Language :: Python :: 2.4',
          'Programming Language :: Python :: 2.5',
          'Programming Language :: Python :: 2.6',
          'Programming Language :: Python :: 2.7',
          'Programming Language :: Python :: 3.0',
          'Topic :: Software Development :: Libraries :: Python Modules',
          ]
      )
