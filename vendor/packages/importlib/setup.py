from distutils.core import setup
import sys


if sys.version_info[0] == 2 and sys.version_info[1] >= 7:
    raise Exception("importlib is included in Python 2.7 and newer for 2.x")
elif sys.version_info[0] == 3 and sys.version_info[1] >= 1:
    raise Exception("importlib is included in Python 3.1 and newer for 3.x")


version_classifiers = ['Programming Language :: Python :: %s' % version
                        for version in ['2', '2.3', '2.4', '2.5', '2.6',
                                        '3', '3.0']]
other_classifiers = [
        'Development Status :: 5 - Production/Stable',
        'License :: OSI Approved :: Python Software Foundation License',
    ]

readme_file = open('README', 'r')
try:
    detailed_description = readme_file.read()
finally:
    readme_file.close()


setup(
        name='importlib',
        version='1.0.2',
        description='Backport of importlib.import_module() from Python 2.7',
        long_description=detailed_description,
        author='Brett Cannon',
        author_email='brett@python.org',
        url='http://svn.python.org/view/sandbox/trunk/importlib/',
        packages=['importlib'],
        classifiers=version_classifiers + other_classifiers,
    )
