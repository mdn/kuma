import logging
import StringIO

from django.conf import settings
from django.core.files.base import ContentFile

from PIL import Image
from celery.decorators import task

log = logging.getLogger('k.task')


@task(rate_limit='15/m')
def generate_thumbnail(for_obj, from_field, to_field,
                       max_size=settings.THUMBNAIL_SIZE):
    """Generate a thumbnail, given a model instance with from and to fields.

    Optionally specify a max_size.

    """

    from_ = getattr(for_obj, from_field)
    to_ = getattr(for_obj, to_field)

    log_msg = 'Generating thumbnail for {model} {id}: {from_f} -> {to_f}'
    log.info(log_msg.format(model=for_obj.__class__.__name__, id=for_obj.id,
                            from_f=from_field, to_f=to_field))
    thumb_content = _create_image_thumbnail(from_.path, longest_side=max_size)
    file_path = from_.path
    if to_:  # Clean up old file before creating new one.
        to_.delete(save=False)
    # Don't modify the object.
    to_.save(file_path, thumb_content, save=False)
    # Use update to avoid race conditions with updating different fields.
    # E.g. when generating two thumbnails for different fields of a single
    # object.
    for_obj.update(**{to_field: to_.name})


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
