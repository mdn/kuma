import sys

extra = {}
if sys.version_info >= (3, 0):
    extra.update(use_2to3=True)

try:
    from setuptools import setup, find_packages
except ImportError:
    from distutils.core import setup, find_packages

author = "Rune Halvorsen"
email = "runefh@gmail.com"
version = "0.3.1"
desc = """Wraps the best available JSON implementation available in a common interface"""

setup(name='anyjson',
      version=version,
      description=desc,
      long_description=open("README").read(),
      classifiers=[
            'License :: OSI Approved :: BSD License',
            'Intended Audience :: Developers',
            'Programming Language :: Python',
            'Programming Language :: Python :: 2',
            'Programming Language :: Python :: 2.4',
            'Programming Language :: Python :: 2.5',
            'Programming Language :: Python :: 2.6',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3',
            'Programming Language :: Python :: 3.1',
          ],
      keywords='json',
      author=author,
      author_email=email,
      url='http://bitbucket.org/runeh/anyjson',
      license='BSD',
      packages=find_packages(exclude=['ez_setup', 'examples', 'tests']),
      zip_safe=False,
      platforms=["any"],
      test_suite = 'nose.collector',
      **extra
)
