'''
pytz setup script
'''

import pytz, sys, os, os.path

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

me = 'Stuart Bishop'
memail = 'stuart@stuartbishop.net'
packages = ['pytz']
resources = ['zone.tab', 'locales/pytz.pot']
for dirpath, dirnames, filenames in os.walk(os.path.join('pytz', 'zoneinfo')):
    # remove the 'pytz' part of the path
    basepath = dirpath.split(os.path.sep, 1)[1]
    resources.extend([os.path.join(basepath, filename)
                     for filename in filenames])
package_data = {'pytz': resources}

assert len(resources) > 10, 'zoneinfo files not found!'

setup (
    name='pytz',
    version=pytz.VERSION,
    zip_safe=True,
    description='World timezone definitions, modern and historical',
    long_description=open('README.txt','r').read(),
    author=me,
    author_email=memail,
    maintainer=me,
    maintainer_email=memail,
    url='http://pythonhosted.org/pytz',
    license='MIT',
    keywords=['timezone','tzinfo', 'datetime', 'olson', 'time'],
    packages=packages,
    package_data=package_data,
    download_url='http://pypi.python.org/pypi/pytz',
    platforms=['Independant'],
    classifiers = [
        'Development Status :: 6 - Mature',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: MIT License',
        'Natural Language :: English',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries :: Python Modules',
        ],
    )
