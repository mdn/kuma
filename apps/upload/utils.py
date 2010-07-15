import StringIO

from django.conf import settings
from django.core.files.base import ContentFile

from PIL import Image


def scale_dimensions(width, height, longest_side=settings.THUMBNAIL_SIZE):
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


def create_thumbnail(file, longest_side=settings.THUMBNAIL_SIZE):
    """
    Returns a thumbnail file with a set longest side.
    """
    originalImage = Image.open(file.path)

    (width, height) = scale_dimensions(file.width, file.height, longest_side)
    resizedImage = originalImage.resize((width, height), Image.ANTIALIAS)

    io = StringIO.StringIO()
    resizedImage.save(io, 'JPEG')

    return ContentFile(io.getvalue())
