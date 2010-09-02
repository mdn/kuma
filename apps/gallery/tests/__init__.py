from django.contrib.auth.models import User
from django.core.files import File

from gallery.models import Image


def image(file_and_save=True, **kwargs):
    """Return a saved image"""
    u = None
    if 'creator' not in kwargs:
        try:
            u = User.objects.get(username='testuser')
        except User.DoesNotExist:
            u = User(username='testuser', email='me@nobody.test')
            u.save()

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
