from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from tower import ugettext_lazy as _lazy

MSG_IMAGE_REQUIRED = _lazy(u'You have not selected an image to upload.')
MSG_IMAGE_LONG = _lazy(
    'Please keep the length of your image filename to %(max)s '
    'characters or less. It is currently %(length)s characters.')
MSG_IMAGE_EXTENSION = _lazy(u'Please upload an image with one of the '
                            u'following extensions: jpg, jpeg, png, gif.')
ALLOWED_IMAGE_EXTENSIONS = ('jpg', 'jpeg', 'png', 'gif')


class ImageAttachmentUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField(error_messages={'required': MSG_IMAGE_REQUIRED,
                                             'max_length': MSG_IMAGE_LONG},
                             max_length=settings.MAX_FILENAME_LENGTH)

    def clean(self):
        c = super(ImageAttachmentUploadForm, self).clean()
        clean_image_extension(c.get('image'))
        return c


def clean_image_extension(form_field):
    """Ensure only images of certain extensions can be uploaded."""
    if form_field:
        if '.' not in form_field.name:
            raise ValidationError(MSG_IMAGE_EXTENSION)
        _, ext = form_field.name.rsplit('.', 1)
        if ext.lower() not in ALLOWED_IMAGE_EXTENSIONS:
            raise ValidationError(MSG_IMAGE_EXTENSION)
