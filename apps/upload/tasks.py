import logging
import StringIO

from django.conf import settings
from django.core.files.base import ContentFile

from PIL import Image
from celery.decorators import task

log = logging.getLogger('k.task')


@task(rate_limit='15/m')
def generate_thumbnail(image, image_name):
    """Generate a thumbnail given an image and a name."""
    log.info('Generating thumbnail for ImageAttachment %s.' % image.id)
    thumb_content = _create_thumbnail(image.file.path)
    image.thumbnail.save(image_name, thumb_content, save=True)


def _create_thumbnail(file_path, longest_side=settings.THUMBNAIL_SIZE):
    """
    Returns a thumbnail file with a set longest side.
    """
    originalImage = Image.open(file_path)
    originalImage = originalImage.convert("RGB")
    (file_width, file_height) = originalImage.size

    (width, height) = _scale_dimensions(file_width, file_height, longest_side)
    resizedImage = originalImage.resize((width, height), Image.ANTIALIAS)

    io = StringIO.StringIO()
    resizedImage.save(io, 'JPEG')

    return ContentFile(io.getvalue())


def _scale_dimensions(width, height, longest_side=settings.THUMBNAIL_SIZE):
    """
    Returns a tuple (width, height), both smaller than longest side, and
    preserves scale.
    """

    if width < longest_side and height < longest_side:
        return (width, height)

    if width > height:
        new_width = longest_side
        new_height = (new_width * height) / width
        return (new_width, new_height)

    new_height = longest_side
    new_width = (new_height * width) / height
    return (new_width, new_height)
