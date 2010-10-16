from django import forms
from django.conf import settings

from tower import ugettext_lazy as _lazy

MSG_IMAGE_REQUIRED = _lazy(u'You have not selected an image to upload.')
MSG_IMAGE_LONG = _lazy(
    'Please keep the length of your image filename to %(max)s '
    'characters or less. It is currently %(length)s characters.')


class ImageAttachmentUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField(error_messages={'required': MSG_IMAGE_REQUIRED,
                                             'max_length': MSG_IMAGE_LONG},
                             max_length=settings.MAX_FILENAME_LENGTH)
