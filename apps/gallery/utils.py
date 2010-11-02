from django.conf import settings
from django.core.files import File

from sumo.urlresolvers import reverse
from .forms import ImageUploadFormAsync, VideoUploadFormAsync
from .models import Image, Video
from upload.utils import upload_media, check_file_size
from upload.tasks import generate_image_thumbnail, _scale_dimensions


def create_image(files, user):
    """Given an uploaded file, a user, and other data, it creates an Image"""
    up_file = files.values()[0]
    check_file_size(up_file, settings.IMAGE_MAX_FILESIZE)

    # Async uploads fallback to these defaults.
    title = u'draft %s' % user.pk
    description = u'Autosaved draft.'
    # Use default locale to make sure a user can only have one draft
    locale = settings.WIKI_DEFAULT_LANGUAGE

    image = Image(title=title, creator=user, locale=locale,
                  description=description)
    image.file.save(up_file.name, File(up_file), save=True)

    # Generate thumbnail off thread
    generate_image_thumbnail.delay(image, up_file.name)

    (width, height) = _scale_dimensions(image.file.width, image.file.height)
    delete_url = reverse('gallery.delete_media', args=['image', image.id])
    return {'name': up_file.name, 'url': image.get_absolute_url(),
            'thumbnail_url': image.thumbnail_url_if_set(),
            'width': width, 'height': height,
            'delete_url': delete_url}


def upload_image(request):
    """Uploads an image from the request."""
    return upload_media(request, ImageUploadFormAsync, create_image)


def create_video(files, user):
    """Given an uploaded file, a user, and other data, it creates a Video"""
    # Async uploads fallback to these defaults.
    title = u'draft %s' % user.pk
    description = u'Autosaved draft.'
    # Use default locale to make sure a user can only have one draft
    locale = settings.WIKI_DEFAULT_LANGUAGE
    try:
        vid = Video.objects.get(title=title, locale=locale)
    except Video.DoesNotExist:
        vid = Video(title=title, creator=user, description=description,
                    locale=locale)
    for name in files:
        up_file = files[name]
        check_file_size(up_file, settings.VIDEO_MAX_FILESIZE)
        # name is in (webm, ogv, flv) sent from upload_video(), below
        getattr(vid, name).save(up_file.name, up_file, save=False)

    vid.save()
    delete_url = reverse('gallery.delete_media', args=['video', vid.id])
    return {'name': up_file.name, 'url': vid.get_absolute_url(),
            'thumbnail_url': vid.thumbnail_url_if_set(),
            'width': settings.THUMBNAIL_PROGRESS_WIDTH,
            'height': settings.THUMBNAIL_PROGRESS_HEIGHT,
            'delete_url': delete_url}


def upload_video(request):
    """Uploads a video from the request; accepts multiple submitted formats"""
    return upload_media(request, VideoUploadFormAsync, create_video)
