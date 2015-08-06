# -*- coding: utf-8 -*-
from os import unlink
from os.path import dirname, isfile, isdir
from shutil import rmtree
import zipfile

try:
    from cStringIO import StringIO
except ImportError:
    from StringIO import StringIO

from nose.tools import assert_false, eq_, ok_

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.template.defaultfilters import slugify

from constance import config

from kuma.core.tests import override_constance_settings
from kuma.users.tests import UserTestCase

from ..models import Submission
from .. import models
from . import make_users, build_submission, build_hidden_submission


def save_valid_submission(title='hello world',
                          desc='This is a hello world demo'):
    User = get_user_model()
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
    s.screenshot_1.save(
        'screenshot_1.jpg',
        ContentFile(
            open('%s/fixtures/screenshot_1.png' % (dirname(dirname(__file__))))
            .read()
        )
    )
    s.save()
    return s


class DemoPackageTest(UserTestCase):

    def setUp(self):
        super(DemoPackageTest, self).setUp()
        self.user, self.admin_user, self.other_user = make_users()

        build_hidden_submission(self.other_user,
                                'hidden-submission-1')

        self.submission = build_submission(self.user)
        self.old_blacklist = models.DEMO_MIMETYPE_BLACKLIST

        build_hidden_submission(self.other_user,
                                'hidden-submission-2')

    def tearDown(self):
        models.DEMO_MIMETYPE_BLACKLIST = self.old_blacklist
        self.user.delete()

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

        self.assertRaisesMessage(ValidationError,
                                 'ZIP file contains no acceptable files',
                                 s.clean)

        unlink(s.demo_package.path)

    def test_demo_package_index_not_in_root(self):
        """Demo package with no index.html at the root is invalid"""
        s = self.submission

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('play/index.html', """<html> </html>""")
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        self.assertRaisesMessage(ValidationError,
                                 'HTML index not found in ZIP',
                                 s.clean)
        unlink(s.demo_package.path)

    def test_demo_package_no_index(self):
        """Demo package with no index.html at all is invalid"""
        s = self.submission

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('js/demo.js', """alert('hi')""")
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        self.assertRaisesMessage(ValidationError,
                                 'HTML index not found in ZIP',
                                 s.clean)

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

        self.assertRaisesMessage(ValidationError,
                                 'ZIP file contains no acceptable files',
                                 s.clean)

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
        except:
            self.fail("The last zip file should have been okay")

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
        except:
            self.fail("The last zip file should have been okay")

        unlink(s.demo_package.path)

    def test_process_demo_package(self):
        """
        Calling process_demo_package() should result in a directory of demo
        files
        """

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')

        zf.writestr(
            'index.html',
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
        """
        Ensure a demo.html in zip file is normalized to index.html when
        unpacked
        """

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

    @override_constance_settings(DEMO_MAX_FILESIZE_IN_ZIP=1024 * 1024)
    def test_demo_file_size_limit(self):
        """Demo package with any individual file >1MB in size is invalid"""
        s = self.submission

        # HACK: Since the field's already defined, it won't pick up the
        # settings change,
        # so force it directly in the field
        s.demo_package.field.max_upload_size = (
            config.DEMO_MAX_FILESIZE_IN_ZIP
        )

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('index.html', """<html> </html>""")
        zf.writestr('bigfile.txt',
                    'x' * (config.DEMO_MAX_FILESIZE_IN_ZIP + 1))
        zf.close()
        s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        self.assertRaisesMessage(ValidationError,
                                 'ZIP file contains a file that is too large: bigfile.txt',
                                 s.clean)

        unlink(s.demo_package.path)

    def test_demo_file_type_blacklist(self):
        """
        Demo package cannot contain files whose detected types are
        blacklisted
        """

        sub_fout = StringIO()
        sub_zf = zipfile.ZipFile(sub_fout, 'w')
        sub_zf.writestr('hello.txt', 'I am some hidden text')
        sub_zf.close()

        # TODO: Need more file types?
        types = (
            (['text/plain'], 'Hi there, I am bad'),
            (['application/zip', 'application/x-zip'], sub_fout.getvalue()),
        )

        for blist, fdata in types:
            models.DEMO_MIMETYPE_BLACKLIST = blist

            s = self.submission

            fout = StringIO()
            zf = zipfile.ZipFile(fout, 'w')
            zf.writestr('index.html', """<html> </html>""")
            zf.writestr('badfile', fdata)
            zf.close()

            s.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

            self.assertRaisesMessage(ValidationError,
                                     'ZIP file contains an unacceptable file: badfile',
                                     s.clean)

    @override_constance_settings(DEMO_BLACKLIST_OVERRIDE_EXTENSIONS="yada")
    def test_demo_blacklist_override(self):
        """bug 1095649"""
        sub_fout = StringIO()
        sub_zf = zipfile.ZipFile(sub_fout, 'w')
        sub_zf.writestr('hello.txt', 'I am some hidden text')
        sub_zf.close()

        models.DEMO_MIMETYPE_BLACKLIST = ['application/zip', 'application/x-zip']

        fout = StringIO()
        zf = zipfile.ZipFile(fout, 'w')
        zf.writestr('index.html', """<html> </html>""")
        zf.writestr('yada.yada', sub_fout.getvalue())
        zf.close()

        self.submission.demo_package.save('play_demo.zip', ContentFile(fout.getvalue()))

        try:
            self.submission.clean()
        except ValidationError:
            self.fail("Shouldn't have failed on cleaning "
                      "a overridded blacklist mimetype")

    def test_hidden_demo_next_prev(self):
        """Ensure hidden demos do not display when next() or previous() are called"""
        s = self.submission

        eq_(s.previous(), None)
        eq_(s.next(), None)

    def test_hidden_demo_shows_to_creator_and_admin(self):
        s = self.submission
        s.hidden = True

        assert_false(s.allows_managing_by(self.other_user))
        assert_false(s.allows_viewing_by(self.other_user))
        ok_(s.allows_managing_by(self.user))
        ok_(s.allows_managing_by(self.admin_user))

    def test_censored_demo_shows_only_in_admin_interface(self):
        s = self.submission
        s.censor()

        assert_false(s.allows_viewing_by(self.other_user))
        assert_false(s.allows_viewing_by(self.user))
        assert_false(s.allows_viewing_by(self.admin_user))
        try:
            ok_(False, Submission.objects.get(id=s.id))
        except Submission.DoesNotExist:
            ok_(True, 'Submission matching query does not exist')
        ok_(Submission.admin_manager.get(id=s.id))

    def test_censored_demo_files_are_deleted(self):
        """Demo files should be deleted when the demo is censored."""
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
        ok_(isfile(s.demo_package.path))
        ok_(isfile('%s/index.html' % path))
        ok_(isfile('%s/css/main.css' % path))
        ok_(isfile('%s/js/main.js' % path))

        s.censor(url="http://example.com/censored-explanation")

        ok_(not isfile(s.demo_package.path))
        ok_(not isfile('%s/index.html' % path))
        ok_(not isfile('%s/css/main.css' % path))
        ok_(not isfile('%s/js/main.js' % path))
        ok_(not isdir(path))
