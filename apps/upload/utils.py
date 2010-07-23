import StringIO

from django.conf import settings
from django.core.files.base import ContentFile

from PIL import Image

from sumo.helpers import reverse
from .forms import ImageUploadForm
from .models import ImageAttachment


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


def create_thumbnail(file_path, longest_side=settings.THUMBNAIL_SIZE):
    """
    Returns a thumbnail file with a set longest side.
    """
    originalImage = Image.open(file_path)
    (file_width, file_height) = originalImage.size

    (width, height) = scale_dimensions(file_width, file_height, longest_side)
    resizedImage = originalImage.resize((width, height), Image.ANTIALIAS)

    io = StringIO.StringIO()
    resizedImage.save(io, 'JPEG')

    return ContentFile(io.getvalue())


def create_image_attachment(up_file, obj, user):
    """
    Given an uploaded file, a user and an object, it creates an ImageAttachment
    owned by `user` and attached to `obj`.
    """
    image = ImageAttachment(content_object=obj, creator=user)
    image.file.save(up_file.name, ContentFile(up_file.read()))
    thumb_content = create_thumbnail(image.file.path)
    image.thumbnail.save(up_file.name, thumb_content)
    image.save()

    return image


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

            image = create_image_attachment(up_file, obj, request.user)

            delete_url = reverse('upload.del_image_async', args=[image.id])
            files.append({'name': up_file.name, 'url': image.file.url,
                          'thumbnail_url': image.thumbnail.url,
                          'width': image.thumbnail.width,
                          'height': image.thumbnail.height,
                          'delete_url': delete_url})
        return files
    return None
