from django.core.files import File

from gallery.models import Image, Video
from sumo.tests import get_user


def image(file_and_save=True, **kwargs):
    """Return a saved image.

    Requires a users fixture if no creator is provided.

    """
    u = None
    if 'creator' not in kwargs:
        u = get_user()

    defaults = {'title': 'Some title', 'description': 'Some description',
                'creator': u}
    defaults.update(kwargs)

    img = Image(**defaults)
    if not file_and_save:
        return img

    if 'file' not in kwargs:
        with open('apps/upload/tests/media/test.jpg') as f:
            up_file = File(f)
            img.file.save(up_file.name, up_file, save=True)

    return img


def video(file_and_save=True, **kwargs):
    """Return a saved video.

    Requires a users fixture if no creator is provided.

    """
    u = None
    if 'creator' not in kwargs:
        u = get_user()

    defaults = {'title': 'Some title', 'description': 'Some description',
                'creator': u}
    defaults.update(kwargs)

    vid = Video(**defaults)
    if not file_and_save:
        return vid

    if 'file' not in kwargs:
        with open('apps/gallery/tests/media/test.webm') as f:
            up_file = File(f)
            vid.webm.save(up_file.name, up_file, save=False)
        with open('apps/gallery/tests/media/test.ogv') as f:
            up_file = File(f)
            vid.ogv.save(up_file.name, up_file, save=False)
        with open('apps/gallery/tests/media/test.flv') as f:
            up_file = File(f)
            vid.flv.save(up_file.name, up_file, save=False)
        vid.save()

    return vid
