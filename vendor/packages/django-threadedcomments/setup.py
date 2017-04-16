from setuptools import setup, find_packages

setup(
    name='django-threadedcomments',
    version='0.5.2',
    description='A simple yet flexible threaded commenting system.',
    author='Eric Florenzano',
    author_email='floguy@gmail.com',
    url='http://code.google.com/p/django-threadedcomments/',
    keywords='django,pinax,comments',
    license='BSD',
    packages=[
        'threadedcomments',
        'threadedcomments.templatetags',
        'threadedcomments.management',
        'threadedcomments.management.commands',
        'threadedcomments.tests',
    ],
    package_data={
        'threadedcomments' : [
            'templates/comment_utils/*.txt',
            'templates/threadedcomments/*.html',
            'templates/threadedcomments_base.html'
        ],
    },
    include_package_data=True,
    zip_safe=False,
    classifiers = [
        'Development Status :: 4 - Beta',
        'Environment :: Web Environment',
        'Intended Audience :: Developers',
        'License :: OSI Approved :: BSD License',
        'Operating System :: OS Independent',
        'Programming Language :: Python',
        'Topic :: Utilities',
    ],
)
