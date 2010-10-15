from datetime import datetime
from glob import iglob
from optparse import make_option
from os import stat, path
import StringIO

from django.conf import settings
from django.contrib.auth.models import User
from django.core.files import File
from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand

from multidb.pinning import pin_this_thread
import PIL

from gallery.models import Image
from upload.tasks import generate_image_thumbnail


ANONYMOUS_USER_NAME = 'AnonymousUser'
IMAGE_DESCRIPTION = 'This image was automatically migrated.'
OLD_PATH = settings.MEDIA_ROOT + '/uploads/gallery/wiki_up/'


class FileTooLargeError(Exception):
    pass


def check_file_size(f, max_allowed_size=settings.IMAGE_MAX_FILESIZE):
    """Check the file size of f is less than max_allowed_size

    Raise FileTooLargeError if the check fails.

    """
    if f.size > max_allowed_size:
        message = '"%s" is too large (%sKB), the limit is %sKB' % (
            f.name, f.size >> 10, max_allowed_size >> 10)
        raise FileTooLargeError(message)


def get_image_user():
    return User.objects.get(username=ANONYMOUS_USER_NAME)


def create_image(file, title, description):
    """Given an uploaded file, a user, and other data, it creates an Image."""
    created = datetime.fromtimestamp(stat(file.name).st_mtime)
    img = Image(title=title, creator=get_image_user(),
                created=created,
                updated=created,
                description=description,
                locale=settings.WIKI_DEFAULT_LANGUAGE)
    try:
        check_file_size(file)
        file_name = file.name
    except FileTooLargeError:
        # Shrink the file down
        old_size = file.size
        originalImage = PIL.Image.open(file.name)
        originalImage = originalImage.convert('RGB')
        width, height = originalImage.size
        percent_shrink = file.size * 1.0 / settings.IMAGE_MAX_FILESIZE
        width = int(width / percent_shrink)
        height = int(height / percent_shrink)
        resizedImage = originalImage.resize((width, height),
                                            PIL.Image.ANTIALIAS)
        io = StringIO.StringIO()
        resizedImage.save(io, 'JPEG')
        file = ContentFile(io.getvalue())
        file_name = title
        print 'Image %s shrunk from %sKB to %sKB.' % (
            file_name, old_size >> 10, file.size >> 10)

        check_file_size(file)
    img.file.save(file_name, file, save=True)
    try:
        generate_image_thumbnail(img, file_name)
    except IOError:
        # Not an actual image
        img.delete()
        return None
    return img


def files_dict(iglob_path):
    files = set()
    for file in iglob(iglob_path):
        if '.' not in file:
            continue
        id, extension = file.rsplit('.', 1)
        file = '.'.join([id, extension.lower()])
        files.add(file)
    return files


def migrate_image(filepath, verbosity=0):
    image_file = open(filepath)
    upload_file = File(image_file)

    title = path.basename(filepath)
    if Image.objects.filter(
            title=title,
            locale=settings.WIKI_DEFAULT_LANGUAGE).exists():
        # Already exists? Skip it. Allows for resume operations
        return False

    if verbosity > 1:
        print 'Processing %s...' % title

    img = create_image(upload_file,
                       title,              # Title
                       IMAGE_DESCRIPTION)  # Description
    if not img:
        print 'Not an image or failed to generate thumbnail for %s' % (
              title)

    # Close and clean up
    image_file.close()

    return True


class Command(BaseCommand):
    help = ('Migrate images. Optional path to old images [--old].'
            ' (Trailing slash optional.)\n\nPass in an integer (default 1) to '
            'specify how many images to migrate, or use "all". E.g.\n\n'
            'python manage.py migrate_images --old /full/path/to/old all')
    option_list = BaseCommand.option_list + (
        make_option('--old',
            action='store',
            dest='old',
            default=OLD_PATH,
            help='Path to the old images.'),
        )

    max_images = 1  # max number of images to migrate, overwrite with 1st arg

    def handle(self, *args, **options):
        pin_this_thread()

        options['verbosity'] = int(options['verbosity'])

        if args:
            try:
                self.max_images = int(args[0])
            except ValueError:
                import sys
                self.max_images = sys.maxint

        if options['verbosity'] > 0:
            print 'Starting migration of images...'

        files = files_dict(options['old'] + '*')

        count = 0
        for filepath in files:
            try:
                if not migrate_image(filepath, options['verbosity']):
                    continue
            except FileTooLargeError, e:
                print e
            count += 1
            if count == self.max_images:
                break

        if options['verbosity'] > 0 and self.max_images == count:
            print 'Reached maximum number of images (%s).' % count
        else:
            print 'Migrated %s images.' % count
