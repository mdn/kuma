from django.conf import settings
from django.core.files import File

from tower import ugettext as _

from sumo.helpers import reverse
from .forms import ImageUploadForm
from .models import ImageAttachment
from .tasks import generate_thumbnail, _scale_dimensions


def create_image_attachment(up_file, obj, user):
    """
    Given an uploaded file, a user and an object, it creates an ImageAttachment
    owned by `user` and attached to `obj`.
    """
    image = ImageAttachment(content_object=obj, creator=user)
    file_ = File(up_file)
    image.file.save(up_file.name, file_, save=False)
    image.save()

    # Generate thumbnail off thread
    generate_thumbnail.delay(image, up_file.name)

    return image


class FileTooLargeError(Exception):
    pass


def upload_images(request, obj):
    """
    Takes in a request object and returns a list with information about each
    image: name, url, thumbnail_url, width, height.

    Attaches images to the given object.
    """
    form = ImageUploadForm(request.POST, request.FILES)
    if request.method == 'POST' and form.is_valid():
        files = []
        for name in request.FILES:
            up_file = request.FILES[name]
            if up_file.size > settings.IMAGE_MAX_FILESIZE:
                message = _('"%s" is too large (%sKB), the limit is %sKB') % (
                    up_file.name, up_file.size >> 10,
                    settings.IMAGE_MAX_FILESIZE >> 10)
                raise FileTooLargeError(message)

            image = create_image_attachment(up_file, obj, request.user)

            delete_url = reverse('upload.del_image_async', args=[image.id])
            im = image.file
            (width, height) = _scale_dimensions(im.width, im.height)
            files.append({'name': up_file.name, 'url': image.file.url,
                          'thumbnail_url': image.thumbnail.url,
                          'width': width,
                          'height': height,
                          'delete_url': delete_url})
        return files
    return None
