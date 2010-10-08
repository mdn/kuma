from datetime import datetime
from fnmatch import fnmatch
from glob import iglob
from optparse import make_option
from os import stat

from django.conf import settings
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.core.files import File
from django.core.management.base import BaseCommand

from multidb.pinning import pin_this_thread

from gallery.models import Video


ANONYMOUS_USER_NAME = 'AnonymousUser'
VIDEO_DESCRIPTION = 'This video was automatically migrated.'
OLD_PATH = settings.MEDIA_ROOT + '/uploads/gallery/old/'


class MissingFlashException(Exception):
    """Raised when missing the flash version of a video."""


class FileTooLargeError(Exception):
    pass


def check_file_size(f, max_allowed_size=settings.VIDEO_MAX_FILESIZE):
    """Check the file size of f is less than max_allowed_size

    Raise FileTooLargeError if the check fails.

    """
    if f.size > max_allowed_size:
        message = '"%s" is too large (%sKB), the limit is %sKB' % (
            f.name, f.size >> 10, max_allowed_size >> 10)
        raise FileTooLargeError(message)


def get_video_user():
    return User.objects.get(username=ANONYMOUS_USER_NAME)


def build_filepath(key, ext):
    return key + '.' + ext


def create_video(files, title, description):
    """Given an uploaded file, a user, and other data, it creates a Video"""
    for name in files:
        up_file = files[name]
        created = datetime.fromtimestamp(stat(up_file.name).st_mtime)
    vid = Video(title=title, creator=get_video_user(),
                created=created,
                updated=created,
                description=description,
                locale=settings.WIKI_DEFAULT_LANGUAGE)
    for name in files:
        up_file = files[name]
        check_file_size(up_file)
        # name is in (webm, ogv, flv) sent from upload_video(), below
        getattr(vid, name).save(up_file.name, up_file, save=False)

    try:
        vid.clean()
    except ValidationError, e:
        return {'validation': e.messages}
    vid.save()
    return vid


def files_dict(iglob_path):
    files = {}
    for file in iglob(iglob_path):
        if not (fnmatch(file, '*.ogg') or fnmatch(file, '*.ogv') or
                fnmatch(file, '*.flv') or fnmatch(file, '*.swf')):
            continue

        id, extension = file.rsplit('.', 1)
        if not id in files:
            files[id] = set()
        files[id].add(extension)
    return files


def migrate_video(file_prefix, extensions, verbosity=0):
    # Check extensions, flv:
    if 'flv' in extensions:
        flv_ext = 'flv'
    elif 'swf' in extensions:
        flv_ext = 'swf'
    else:  # Flash is required
        raise MissingFlashException(file_prefix)
    # then check ogg:
    ogg_ext = ''
    if 'ogv' in extensions:
        ogg_ext = 'ogv'
    elif 'ogg' in extensions:
        ogg_ext = 'ogg'

    # open up the files and add them to the list of to-be-uploaded
    flv_f = open(build_filepath(file_prefix, flv_ext))
    upload_files = {'flv': File(flv_f)}

    if ogg_ext:
        ogg_f = open(build_filepath(file_prefix, ogg_ext))
        upload_files['ogv'] = File(ogg_f)

    _, title = file_prefix.rsplit('/', 1)
    if Video.objects.filter(
            title=title,
            locale=settings.WIKI_DEFAULT_LANGUAGE).exists():
        # Already exists? Skip it.
        return False

    if verbosity > 1:
        print 'Processing %s [%s]...' % (title, ', '.join(extensions))

    create_video(upload_files,
                 title,              # Title
                 VIDEO_DESCRIPTION)  # Description

    # Close and clean up
    flv_f.close()
    if ogg_ext:
        ogg_f.close()

    return True


class Command(BaseCommand):
    help = ('Migrate screencasts. Optional path to old videos [--old].'
            ' (Trailing slash required.)\n\nPass in an integer (default 1) to '
            'specify how many videos to migrate, or use "all". E.g.\n\n'
            'python manage.py migrate_videos --old /full/path/to/old all')
    option_list = BaseCommand.option_list + (
        make_option('--old',
            action='store',
            dest='old',
            default=OLD_PATH,
            help='Path to the old videos.'),
        )

    max_videos = 1  # max number of videos to migrate, overwrite with 1st arg

    def handle(self, *args, **options):
        pin_this_thread()

        options['verbosity'] = int(options['verbosity'])

        if args:
            try:
                self.max_videos = int(args[0])
            except ValueError:
                import sys
                self.max_videos = sys.maxint

        if options['verbosity'] > 0:
            print 'Starting migration of videos...'

        files = files_dict(options['old'] + '*')

        count = 0
        for file_prefix, extensions in files.iteritems():
            if not migrate_video(file_prefix, extensions,
                                 options['verbosity']):
                continue
            count += 1
            if count == self.max_videos:
                break

        if options['verbosity'] > 0 and self.max_videos == count:
            print 'Reached maximum number of videos (%s).' % count
        else:
            print 'Migrated %s videos.' % count
