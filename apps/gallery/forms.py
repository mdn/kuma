from django import forms

from tower import ugettext_lazy as _lazy

from gallery.models import Image, Video
from sumo.form_fields import StrippedCharField

# Error messages
MSG_TITLE_REQUIRED = _lazy(u'Please provide a title.')
MSG_TITLE_SHORT = _lazy(
    'The title is too short (%(show_value)s characters). It must be at '
    'least %(limit_value)s characters.')
MSG_TITLE_LONG = _lazy(
    'Please keep the length of your title to %(limit_value)s characters '
    'or less. It is currently %(show_value)s characters.')
MSG_DESCRIPTION_REQUIRED = _lazy(u'Please provide a description.')
MSG_DESCRIPTION_LONG = _lazy(
    'Please keep the length of your description to %(limit_value)s '
    'characters or less. It is currently %(show_value)s characters.')
MSG_IMAGE_REQUIRED = _lazy(u'You have not selected an image to upload.')


class ImageUploadForm(forms.ModelForm):
    """Image upload form."""
    file = forms.ImageField(error_messages={'required': MSG_IMAGE_REQUIRED})
    title = StrippedCharField(
        min_length=5, max_length=255,
        error_messages={'required': MSG_TITLE_REQUIRED,
                        'min_length': MSG_TITLE_SHORT,
                        'max_length': MSG_TITLE_LONG})
    description = StrippedCharField(
        max_length=10000, widget=forms.Textarea(),
        error_messages={'required': MSG_DESCRIPTION_REQUIRED,
                        'max_length': MSG_DESCRIPTION_LONG})

    class Meta:
        model = Image
        fields = ('file', 'title', 'description')


class VideoUploadForm(forms.ModelForm):
    """Video upload form."""
    webm = forms.FileField(required=False)
    ogv = forms.FileField(required=False)
    flv = forms.FileField(required=False)
    title = StrippedCharField(
        min_length=5, max_length=255,
        error_messages={'required': MSG_TITLE_REQUIRED,
                        'min_length': MSG_TITLE_SHORT,
                        'max_length': MSG_TITLE_LONG})
    description = StrippedCharField(
        max_length=10000, widget=forms.Textarea(),
        error_messages={'required': MSG_DESCRIPTION_REQUIRED,
                        'max_length': MSG_DESCRIPTION_LONG})

    class Meta:
        model = Video
        fields = ('webm', 'ogv', 'flv', 'title', 'description')
