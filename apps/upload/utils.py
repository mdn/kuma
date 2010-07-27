from django.core.files import File

from sumo.helpers import reverse
from .forms import ImageUploadForm
from .models import ImageAttachment
from .tasks import generate_thumbnail


def create_image_attachment(up_file, obj, user):
    """
    Given an uploaded file, a user and an object, it creates an ImageAttachment
    owned by `user` and attached to `obj`.
    """
    image = ImageAttachment(content_object=obj, creator=user)
    file_ = File(up_file)
    image.file.save(up_file.name, file_, save=False)
    image.thumbnail.save(up_file.name, file_, save=False)
    image.save()

    # Generate thumbnail off thread
    generate_thumbnail.delay(image, up_file.name)

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
