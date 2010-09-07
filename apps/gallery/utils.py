from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.files import File

from sumo.urlresolvers import reverse
from .forms import ImageUploadForm, VideoUploadForm
from .models import Image, Video
from upload.utils import upload_media, check_file_size
from upload.tasks import generate_image_thumbnail, _scale_dimensions


def create_image(files, user, max_allowed_size, title, description, locale):
    """Given an uploaded file, a user, and other data, it creates an Image"""
    up_file = files.values()[0]
    check_file_size(up_file, max_allowed_size)

    image = Image(title=title, creator=user, locale=locale,
                  description=description)
    image.file.save(up_file.name, File(up_file), save=True)

    # Generate thumbnail off thread
    generate_image_thumbnail.delay(image, up_file.name)

    (width, height) = _scale_dimensions(image.file.width, image.file.height)
    delete_url = reverse('gallery.del_media_async', args=['image', image.id])
    return {'name': up_file.name, 'url': image.get_absolute_url(),
            'thumbnail_url': image.thumbnail_url_if_set(),
            'width': width, 'height': height,
            'delete_url': delete_url}


def upload_image(request):
    """Uploads an image from the request."""
    title = request.POST.get('title')
    description = request.POST.get('description')
    return upload_media(
        request, ImageUploadForm, create_image, settings.IMAGE_MAX_FILESIZE,
        title=title, description=description, locale=request.locale)


def create_video(files, user, max_allowed_size, title, description, locale):
    """Given an uploaded file, a user, and other data, it creates a Video"""
    vid = Video(title=title, creator=user, description=description,
                locale=locale)
    for name in files:
        up_file = files[name]
        check_file_size(up_file, max_allowed_size)
        # name is in (webm, ogv, flv) sent from upload_video(), below
        getattr(vid, name).save(up_file.name, up_file, save=False)

    try:
        vid.clean()
    except ValidationError, e:
        return {'validation': e.messages}
    vid.save()
    delete_url = reverse('gallery.del_media_async', args=['video', vid.id])
    return {'name': up_file.name, 'url': vid.get_absolute_url(),
            'thumbnail_url': vid.thumbnail_url_if_set(),
            'width': settings.THUMBNAIL_SIZE,
            'height': settings.THUMBNAIL_SIZE,
            'delete_url': delete_url}


def upload_video(request):
    """Uploads a video from the request; accepts multiple submitted formats"""
    title = request.POST.get('title')
    description = request.POST.get('description')
    return upload_media(
        request, VideoUploadForm, create_video, settings.VIDEO_MAX_FILESIZE,
        title=title, description=description, locale=request.locale)
