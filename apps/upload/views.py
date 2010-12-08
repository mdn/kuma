import json

from django.views.decorators.http import require_POST
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import get_model
from django.http import (HttpResponse, HttpResponseNotFound,
                         HttpResponseBadRequest)

from commonware.decorators import xframe_sameorigin
from tower import ugettext as _

from access.decorators import has_perm_or_owns_or_403, login_required
from upload.models import ImageAttachment
from upload.utils import upload_imageattachment, FileTooLargeError


@login_required
@require_POST
@xframe_sameorigin
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
        file_info = upload_imageattachment(request, obj)
    except FileTooLargeError as e:
        return HttpResponseBadRequest(
            json.dumps({'status': 'error', 'message': e.args[0]}))

    if isinstance(file_info, dict) and 'thumbnail_url' in file_info:
        return HttpResponse(
            json.dumps({'status': 'success', 'file': file_info}))

    message = _('Invalid or no image received.')
    return HttpResponseBadRequest(
        json.dumps({'status': 'error', 'message': message,
                    'errors': file_info}))


@login_required
@require_POST
@xframe_sameorigin
@has_perm_or_owns_or_403('upload.image_upload', 'creator',
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
