import json

from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import get_model
from django.http import HttpResponse, HttpResponseServerError

from tower import ugettext as _

from .forms import ImageUploadForm
from .models import ImageAttachment
from .utils import create_thumbnail


def up_image_async(request, model_name, object_pk):
    """Upload all images in request.FILES."""

    # Lookup the model's content type
    m = get_model(*model_name.split('.'))
    if m is None:
        return _raise_error_async(request, 'Model does not exist.')

    # Then look up the object by pk
    if object_pk is not None:
        try:
            obj = m.objects.get(pk=object_pk)
        except ObjectDoesNotExist:
            return _raise_error_async(request, 'Object does not exist.')

    form = ImageUploadForm(request.POST, request.FILES)

    if request.method == 'POST' and form.is_valid():
        files = []
        for name in request.FILES:
            up_file = request.FILES[name]

            image = ImageAttachment(content_object=obj, creator=request.user)
            file_content = ContentFile(up_file.read())
            image.file.save(up_file.name, file_content)
            thumb_content = create_thumbnail(image.file)
            image.thumbnail.save(up_file.name, thumb_content)
            image.save()

            files.append({'name': up_file.name, 'url': image.file.url,
                          'thumbnail_url': image.thumbnail.url,
                          'width': image.thumbnail.width,
                          'height': image.thumbnail.height})

        return HttpResponse(
            json.dumps({'status': 'success', 'files': files}))

    return _raise_error_async(request, 'Invalid or no image received')


def _raise_error_async(request, message):
    # raise 500 error
    return HttpResponseServerError(
        json.dumps({'status': 'error', 'message': _(message)}))
