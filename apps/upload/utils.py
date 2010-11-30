from django.conf import settings
from django.core.files import File

from tower import ugettext_lazy as _lazy

from upload.forms import ImageAttachmentUploadForm
from upload.models import ImageAttachment
from upload.tasks import generate_image_thumbnail, _scale_dimensions


def check_file_size(f, max_allowed_size):
    """Check the file size of f is less than max_allowed_size

    Raise FileTooLargeError if the check fails.

    """
    if f.size > max_allowed_size:
        message = _lazy('"%s" is too large (%sKB), the limit is %sKB') % (
            f.name, f.size >> 10, max_allowed_size >> 10)
        raise FileTooLargeError(message)


def create_imageattachment(files, user, obj):
    """
    Given an uploaded file, a user and an object, it creates an ImageAttachment
    owned by `user` and attached to `obj`.
    """
    up_file = files.values()[0]
    check_file_size(up_file, settings.IMAGE_MAX_FILESIZE)

    image = ImageAttachment(content_object=obj, creator=user)
    image.file.save(up_file.name, File(up_file), save=True)

    # Generate thumbnail off thread
    generate_image_thumbnail.delay(image, up_file.name)

    (width, height) = _scale_dimensions(image.file.width, image.file.height)
    return {'name': up_file.name, 'url': image.file.url,
            'thumbnail_url': image.thumbnail_if_set().url,
            'width': width, 'height': height,
            'delete_url': image.get_delete_url()}


class FileTooLargeError(Exception):
    pass


def upload_imageattachment(request, obj):
    """Uploads image attachments. See upload_media.

    Attaches images to the given object, using the create_imageattachment
    callback.

    """
    return upload_media(request, ImageAttachmentUploadForm,
                        create_imageattachment, obj=obj)


def upload_media(request, form_cls, up_file_callback, instance=None, **kwargs):
    """
    Uploads media files and returns a list with information about each media:
    name, url, thumbnail_url, width, height.

    Args:
    * request object
    * form class, used to instantiate and validate form for upload
    * callback to save the file given its content and creator
    * extra kwargs will all be passed to the callback

    """
    form = form_cls(request.POST, request.FILES)
    if request.method == 'POST' and form.is_valid():
        return up_file_callback(request.FILES, request.user, **kwargs)
    elif not form.is_valid():
        return form.errors
    return None
