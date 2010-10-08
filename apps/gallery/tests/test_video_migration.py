from django.core.files import File

from nose.tools import eq_

from gallery.models import Video
from gallery.management.commands.migrate_videos import (
    build_filepath, create_video, files_dict, migrate_video)

from sumo.tests import TestCase


class MigrateVideoTestCase(TestCase):
    fixtures = ['users.json']

    def tearDown(self):
        Video.objects.all().delete()
        super(MigrateVideoTestCase, self).tearDown()

    def test_build_filepath(self):
        eq_('file_name.ext', build_filepath('file_name', 'ext'))

    def test_create_video(self):
        with open('apps/gallery/tests/media/test.flv') as flv_f:
            with open('apps/gallery/tests/media/test.ogv') as ogv_f:
                upload_files = {'flv': File(flv_f), 'ogv': File(ogv_f)}
                vid = create_video(upload_files, 'Some title', 'A description')

        eq_('Some title', vid.title)
        eq_('A description', vid.description)
        assert vid.flv is not None, 'flv field is None.'
        assert vid.ogv is not None, 'ogv field is None.'

    def test_files_dict(self):
        eq_({'apps/gallery/tests/media/test': set(['flv', 'ogv'])},
            files_dict('apps/gallery/tests/media/*'))
        eq_({}, files_dict('.*'))

    def test_migrate_video(self):
        file_prefix = 'apps/gallery/tests/media/test'
        eq_(True, migrate_video(file_prefix, ['flv', 'ogv']))
        # 2nd time skips the video
        eq_(False, migrate_video(file_prefix, ['flv', 'ogv']))
        # Make sure there's a video object
        eq_(1, Video.objects.count())
