import logging
import StringIO

from django.conf import settings
from django.core.files.base import ContentFile

from PIL import Image
from celery.decorators import task

log = logging.getLogger('k.task')


@task(rate_limit='15/m')
def generate_image_thumbnail(obj, image_name, field_name='file'):
    """Generate a thumbnail given an image and a name."""
    log.info('Generating thumbnail for %(model_class)s %(id)s.' %
             {'model_class': obj.__class__.__name__, 'id': obj.id})
    field = getattr(obj, field_name)
    thumb_content = _create_image_thumbnail(field.path)
    obj.thumbnail.save(image_name, thumb_content, save=True)


def _create_image_thumbnail(file_path, longest_side=settings.THUMBNAIL_SIZE):
    """
    Returns a thumbnail file with a set longest side.
    """
    originalImage = Image.open(file_path)
    originalImage = originalImage.convert("RGB")
    file_width, file_height = originalImage.size

    width, height = _scale_dimensions(file_width, file_height, longest_side)
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
