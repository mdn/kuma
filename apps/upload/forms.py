from django import forms

from tower import ugettext_lazy as _lazy

MSG_IMAGE_REQUIRED = _lazy(u'You have not selected an image to upload.')


class ImageAttachmentUploadForm(forms.Form):
    """Image upload form."""
    image = forms.ImageField(error_messages={'required': MSG_IMAGE_REQUIRED})
