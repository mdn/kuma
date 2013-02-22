# coding=utf-8

# This Python file uses the following encoding: utf-8
# see also: http://www.python.org/dev/peps/pep-0263/
import sys
import logging
import re
import urlparse
import time
import zipfile
import os
from os import unlink
from os.path import basename, dirname, isfile, isdir
from shutil import rmtree
import datetime

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO


from django.conf import settings
settings.DEMO_MAX_FILESIZE_IN_ZIP = 1 * 1024 * 1024
settings.DEMO_MAX_ZIP_FILESIZE = 1 * 1024 * 1024


from django.http import HttpRequest
from django.test import TestCase
from django.test.client import Client

from django.core.exceptions import ValidationError
from django.contrib.auth.models import User

from django.core.files.base import ContentFile

from django.template.defaultfilters import slugify

from nose.tools import assert_equal, with_setup, assert_false, eq_, ok_
from nose.plugins.attrib import attr

from demos.models import Submission
import demos.models
demos.models.DEMO_MAX_FILESIZE_IN_ZIP = 1 * 1024 * 1024

from demos.forms import SubmissionEditForm, SubmissionNewForm


def save_valid_submission(title='hello world', desc = 'This is a hello world demo'):
    testuser = User.objects.get(username='testuser')
    s = Submission(title=title, slug=slugify(title),
        description=desc,
        summary=desc,
        creator=testuser)
    fout = StringIO()
    zf = zipfile.ZipFile(fout, 'w')
    zf.writestr('index.html', """<html> </html>""")
    zf.close()
    s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))
    s.screenshot_1.save('screenshot_1.jpg', ContentFile(open(
        '%s/fixtures/screenshot_1.png' % ( dirname(dirname(__file__)), ) ).read()))
    s.save()
    return s


class DemoPackageTest(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(
            'tester', 'tester@tester.com', 'tester')
        self.user.save()

        self.admin_user = User.objects.create_superuser(
            'admin_tester', 'admin_tester@tester.com', 'admint_tester')
        self.admin_user.save()

        self.other_user = User.objects.create_user(
            'visitor', 'visitor@visitor.com', 'visitor')
        self.other_user.save()

        hidden_prev_demo = self._build_hidden_submission('hidden-submission-1')

        self.submission = self._build_submission()
        self.old_blacklist = demos.models.DEMO_MIMETYPE_BLACKLIST

        hidden_next_demo = self._build_hidden_submission('hidden-submission-2')

    def tearDown(self):
        demos.models.DEMO_MIMETYPE_BLACKLIST = self.old_blacklist
        self.user.delete()

    def _build_submission(self):
        now = str(datetime.datetime.now())

        s = Submission(title='Hello world' + now, slug='hello-world' + now,
            description='This is a hello world demo', hidden=False,
            creator=self.user)
        s.save()

        return s

    def _build_hidden_submission(self, slug):
        now = str(datetime.datetime.now())

        s = Submission(title='Hidden submission 1' + now, slug=slug + now,
            description='This is a hidden demo', hidden=True,
            creator=self.other_user)
        s.save()

        return s

    def test_demo_package_no_files(self):
        """Demo package with no files is invalid"""

        s = Submission(title='Hello world', slug='hello-world',
            description='This is a hello world demo',
            video_url='http://www.youtube.com/watch?v=dQw4w9WgXcQ',
            creator=self.user)

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            s.clean()
            ok_(False, "There should be a validation exception")
        except ValidationError, e:
            ok_('ZIP file contains no acceptable files' in e.messages)

        unlink(s.demo_package.path)

    def test_demo_package_index_not_in_root(self):
        """Demo package with no index.html at the root is invalid"""
        s = self.submission

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('play/index.html', """<html> </html>""")
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            s.clean()
            ok_(False, "There should be a validation exception")
        except ValidationError, e:
            ok_('HTML index not found in ZIP' in e.messages)

        unlink(s.demo_package.path)

    def test_demo_package_no_index(self):
        """Demo package with no index.html at all is invalid"""
        s = self.submission

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('js/demo.js', """alert('hi')""")
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            s.clean()
            ok_(False, "There should be a validation exception")
        except ValidationError, e:
            ok_('HTML index not found in ZIP' in e.messages)

        unlink(s.demo_package.path)

    def test_demo_package_badfiles(self):
        """Demo package with naughty file entries is invalid"""
        s = self.submission

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('/etc/passwd', """HAXXORED""")
        zf.writestr('../../../../etc/passwd', """HAXXORED""")
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            s.clean()
            ok_(False, "There should be a validation exception")
        except ValidationError, e:
            ok_('ZIP file contains no acceptable files' in e.messages)

        unlink(s.demo_package.path)

    def test_demo_package_valid(self):
        """Demo package with at least index.html in root is valid"""
        s = self.submission

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('index.html', """<html> </html>""")
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            s.clean()
            ok_(True, "This last one should be okay")
        except:
            ok_(False, "The last zip file should have been okay")

        unlink(s.demo_package.path)

    def test_demo_package_also_accept_demo_html(self):
        """Demo package with demo.html in root is valid, too"""
        s = self.submission

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('demo.html', """<html> </html>""")
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            s.clean()
            ok_(True, "This last one should be okay")
        except:
            ok_(False, "The last zip file should have been okay")

        unlink(s.demo_package.path)

    def test_process_demo_package(self):
        """Calling process_demo_package() should result in a directory of demo files"""

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')

        zf.writestr('index.html',
            """<html>
                <head>
                    <link rel="stylesheet" href="css/main.css" type="text/css" />
                </head>
                <body>
                    <h1>Hello world</h1>
                    <script type="text/javascript" src="js/main.js"></script>
                </body>
            </html>""")

        zf.writestr('css/main.css',
            'h1 { color: red }')

        zf.writestr('js/main.js',
            'alert("HELLO WORLD");')

        zf.close()

        s = Submission(title='Hello world', slug='hello-world',
            description='This is a hello world demo',
            creator=self.user)

        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))
        s.demo_package.close()
        s.clean()
        s.save()

        s.process_demo_package()

        path = s.demo_package.path.replace('.zip', '')

        ok_(isdir(path))
        ok_(isfile('%s/index.html' % path))
        ok_(isfile('%s/css/main.css' % path))
        ok_(isfile('%s/js/main.js' % path))

        rmtree(path)

    def test_demo_html_normalized(self):
        """Ensure a demo.html in zip file is normalized to index.html when unpacked"""

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('demo.html', """<html></html""")
        zf.writestr('css/main.css', 'h1 { color: red }')
        zf.writestr('js/main.js', 'alert("HELLO WORLD");')
        zf.close()

        s = Submission(title='Hello world', slug='hello-world',
            description='This is a hello world demo',
            creator=self.user)

        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))
        s.demo_package.close()
        s.clean()
        s.save()

        s.process_demo_package()

        path = s.demo_package.path.replace('.zip', '')

        ok_(isdir(path))
        ok_(isfile('%s/index.html' % path))
        ok_(isfile('%s/css/main.css' % path))
        ok_(isfile('%s/js/main.js' % path))

        rmtree(path)

    def test_demo_unicode_filenames(self):
        """Bug 741660: Demo package containing filenames with non-ASCII
        characters works"""

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('demo.html', """<html></html""")
        zf.writestr('css/예제.css', 'h1 { color: red }')
        zf.writestr('js/示例.js', 'alert("HELLO WORLD");')
        zf.close()

        s = Submission(title='Hello world', slug='hello-world',
            description='This is a hello world demo',
            creator=self.user)

        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))
        s.demo_package.close()
        s.clean()
        s.save()

        s.process_demo_package()

        path = s.demo_package.path.replace('.zip', '')

        ok_(isdir(path))
        ok_(isfile((u'%s/index.html' % path).encode('utf-8')))
        ok_(isfile((u'%s/css/예제.css' % path).encode('utf-8')))
        ok_(isfile((u'%s/js/示例.js' % path).encode('utf-8')))

        rmtree(path)

    def test_demo_unicode_filenames_2(self):
        """Bug 741660: Try testing a real .zip with non-ASCII filenames"""
        zip_fn = '%s/fixtures/css3_clock.zip' % dirname(dirname(__file__))

        zf = zipfile.ZipFile(zip_fn)

        s = Submission(title='Hello world', slug='hello-world',
            description='This is a hello world demo',
            creator=self.user)

        s.demo_package.save('play_demo.zip', ContentFile(open(zip_fn).read()))
        s.demo_package.close()
        s.clean()
        s.save()

        s.process_demo_package()

        path = s.demo_package.path.replace('.zip', '')

        ok_(isdir(path))
        ok_(isfile((u'%s/stylé.css' % path).encode('utf-8')))

        rmtree(path)

    def test_demo_deletion(self):
        """Ensure that demo files are deleted along with submission record"""

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('demo.html', """<html></html""")
        zf.writestr('css/main.css', 'h1 { color: red }')
        zf.writestr('js/main.js', 'alert("HELLO WORLD");')
        zf.close()

        s = Submission(title='Hello world', slug='hello-world',
            description='This is a hello world demo',
            creator=self.user)

        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))
        s.demo_package.close()
        s.clean()
        s.save()

        s.process_demo_package()

        path = s.demo_package.path.replace('.zip', '')

        ok_(isdir(path))
        ok_(isfile('%s/index.html' % path))
        ok_(isfile('%s/css/main.css' % path))
        ok_(isfile('%s/js/main.js' % path))

        s.delete()

        ok_(not isfile('%s/index.html' % path))
        ok_(not isfile('%s/css/main.css' % path))
        ok_(not isfile('%s/js/main.js' % path))
        ok_(not isdir(path))

    def test_demo_file_size_limit(self):
        """Demo package with any individual file >1MB in size is invalid"""
        s = self.submission

        # HACK: Since the field's already defined, it won't pick up the settings change,
        # so force it directly in the field
        s.demo_package.field.max_upload_size = settings.DEMO_MAX_FILESIZE_IN_ZIP

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('index.html', """<html> </html>""")
        zf.writestr('bigfile.txt', ''.join('x' for x in range(0, settings.DEMO_MAX_FILESIZE_IN_ZIP + 1)))
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            s.clean()
            ok_(False, "There should be a validation exception")
        except ValidationError, e:
            ok_('ZIP file contains a file that is too large: bigfile.txt' in e.messages)

        unlink(s.demo_package.path)

    def test_demo_file_type_blacklist(self):
        """Demo package cannot contain files whose detected types are blacklisted"""

        sub_fout = StringIO()
        sub_zf = zipfile.ZipFile(sub_fout, 'w')
        sub_zf.writestr('hello.txt', 'I am some hidden text')
        sub_zf.close()

        # TODO: Need more file types?
        types = (
            (['text/plain'], 'Hi there, I am bad'),
            #( [ 'application/xml' ], '<?xml version="1.0"?><hi>I am bad</hi>' ),
            (['application/zip', 'application/x-zip'], sub_fout.getvalue()),
            #( [ 'image/x-ico' ], open('media/img/favicon.ico','r').read() ),
        )

        for blist, fdata in types:
            demos.models.DEMO_MIMETYPE_BLACKLIST = blist

            s = self.submission

            fout = StringIO()
            zf = zipfile.ZipFile(fout, 'w')
            zf.writestr('index.html', """<html> </html>""")
            zf.writestr('badfile', fdata)
            zf.close()

            s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

            try:
                s.clean()
                ok_(False, "There should be a validation exception")
            except ValidationError, e:
                ok_('ZIP file contains an unacceptable file: badfile' in e.messages)

    def test_hidden_demo_next_prev(self):
        """Ensure hidden demos do not display when next() or previous() are called"""
        s = self.submission

        eq_(s.previous(), None)
        eq_(s.next(), None)

    def test_hidden_demo_shows_to_creator_and_admin(self):
        """Demo package with at least index.html in root is valid"""
        s = self.submission
        s.hidden = True

        assert_false(s.allows_hiding_by(self.other_user))
        assert_false(s.allows_viewing_by(self.other_user))
        ok_(s.allows_hiding_by(self.user))
        ok_(s.allows_hiding_by(self.admin_user))

    def test_censored_demo_shows_only_in_admin_interface(self):
        """Demo package with at least index.html in root is valid"""
        s = self.submission
        s.censored = True
        s.save()

        assert_false(s.allows_viewing_by(self.other_user))
        assert_false(s.allows_viewing_by(self.user))
        assert_false(s.allows_viewing_by(self.admin_user))
        try:
            ok_(False, Submission.objects.get(id=s.id))
        except Submission.DoesNotExist:
            ok_(True, 'Submission matching query does not exist')
        ok_(Submission.admin_manager.get(id=s.id))
