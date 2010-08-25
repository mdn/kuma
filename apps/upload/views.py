import json

from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import get_model
from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseBadRequest)

from tower import ugettext as _

from access.decorators import has_perm_or_owns_or_403
from .models import ImageAttachment
from .utils import upload_images, FileTooLargeError


@login_required
@require_POST
def up_image_async(request, model_name, object_pk):
    """Upload all images in request.FILES."""

    # Lookup the model's content type
    m = get_model(*model_name.split('.'))
    if m is None:
        message = _('Model does not exist.')
        return HttpResponseBadRequest(
            json.dumps({'status': 'error', 'message': message}))

    # Then look up the object by pk
    try:
        obj = m.objects.get(pk=object_pk)
    except ObjectDoesNotExist:
        message = _('Object does not exist.')
        return HttpResponseNotFound(
            json.dumps({'status': 'error', 'message': message}))

    try:
        files = upload_images(request, obj)
    except FileTooLargeError as e:
        return HttpResponseBadRequest(
            json.dumps({'status': 'error', 'message': e.args[0]}))

    if files is not None:
        return HttpResponse(
            json.dumps({'status': 'success', 'files': files}))

    message = _('Invalid or no image received.')
    return HttpResponseBadRequest(
        json.dumps({'status': 'error', 'message': message}))


@login_required
@require_POST
@has_perm_or_owns_or_403('upload_imageattachment.image_upload', 'creator',
                         (ImageAttachment, 'id__iexact', 'image_id'),
                         (ImageAttachment, 'id__iexact', 'image_id'))
def del_image_async(request, image_id):
    """Delete an image given its object id."""
    try:
        image = ImageAttachment.objects.get(pk=image_id)
    except ImageAttachment.DoesNotExist:
        message = _('The requested image could not be found.')
        return HttpResponseNotFound(
            json.dumps({'status': 'error', 'message': message}))

    image.file.delete()
    if image.thumbnail:
        image.thumbnail.delete()
    image.delete()

    return HttpResponse(json.dumps({'status': 'success'}))
