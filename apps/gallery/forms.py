from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError

from tower import ugettext_lazy as _lazy

from gallery import DRAFT_TITLE_PREFIX
from gallery.models import Image, Video
from sumo.form_fields import StrippedCharField
from sumo_locales import LOCALES

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
MSG_IMAGE_LONG = _lazy(
    'Please keep the length of your image filename to %(max)s '
    'characters or less. It is currently %(length)s characters.')
MSG_WEBM_LONG = _lazy(
    'Please keep the length of your webm filename to %(max)s '
    'characters or less. It is currently %(length)s characters.')
MSG_OGV_LONG = _lazy(
    'Please keep the length of your ogv filename to %(max)s '
    'characters or less. It is currently %(length)s characters.')
MSG_FLV_LONG = _lazy(
    'Please keep the length of your flv filename to %(max)s '
    'characters or less. It is currently %(length)s characters.')
MSG_VID_REQUIRED = _lazy('The video has no files associated with it. You must '
                         'upload one of the following extensions: webm, ogv, '
                         'flv.')
MSG_TITLE_DRAFT = _lazy('Please select a different title.')


class ImageUploadFormAsync(forms.Form):
    """Image upload form for async requests."""
    file = forms.ImageField(error_messages={'required': MSG_IMAGE_REQUIRED,
                                            'max_length': MSG_IMAGE_LONG},
                            max_length=settings.MAX_FILENAME_LENGTH)


class ImageForm(forms.ModelForm):
    """Image form."""
    file = forms.ImageField(error_messages={'required': MSG_IMAGE_REQUIRED,
                                            'max_length': MSG_IMAGE_LONG},
                            max_length=settings.MAX_FILENAME_LENGTH)
    locale = forms.ChoiceField(
                    choices=[(LOCALES[k].external, LOCALES[k].native) for
                             k in settings.SUMO_LANGUAGES],
                    initial=settings.WIKI_DEFAULT_LANGUAGE)
    title = StrippedCharField(
        min_length=5, max_length=255,
        error_messages={'required': MSG_TITLE_REQUIRED,
                        'min_length': MSG_TITLE_SHORT,
                        'max_length': MSG_TITLE_LONG})
    description = StrippedCharField(
        max_length=10000, widget=forms.Textarea(),
        error_messages={'required': MSG_DESCRIPTION_REQUIRED,
                        'max_length': MSG_DESCRIPTION_LONG})

    def clean(self):
        c = super(ImageForm, self).clean()
        return clean_draft(self, c)

    def save(self, update_user=None, **kwargs):
        return save_form(self, update_user, **kwargs)

    class Meta:
        model = Image
        fields = ('file', 'locale', 'title', 'description')


class VideoUploadFormAsync(forms.ModelForm):
    """Video upload form for async requests."""
    flv = forms.FileField(required=False,
                          error_messages={'max_length': MSG_FLV_LONG},
                          max_length=settings.MAX_FILENAME_LENGTH)
    ogv = forms.FileField(required=False,
                          error_messages={'max_length': MSG_OGV_LONG},
                          max_length=settings.MAX_FILENAME_LENGTH)
    webm = forms.FileField(required=False,
                           error_messages={'max_length': MSG_WEBM_LONG},
                           max_length=settings.MAX_FILENAME_LENGTH)
    thumbnail = forms.ImageField(required=False,
                                 error_messages={'max_length': MSG_IMAGE_LONG},
                                 max_length=settings.MAX_FILENAME_LENGTH)

    def clean(self):
        c = super(VideoUploadFormAsync, self).clean()
        if not ('webm' in c and c['webm'] and
                    c['webm'].name.endswith('.webm') or
                'ogv' in c and c['ogv'] and
                    (c['ogv'].name.endswith('.ogv') or
                     c['ogv'].name.endswith('.ogg')) or
                'flv' in c and c['flv'] and c['flv'].name.endswith('.flv') or
                'thumbnail' in c and c['thumbnail']):
            raise ValidationError(MSG_VID_REQUIRED)
        return c

    class Meta:
        model = Video
        fields = ('webm', 'ogv', 'flv', 'thumbnail')


class VideoForm(forms.ModelForm):
    """Video form."""
    flv = forms.FileField(required=False,
                          error_messages={'max_length': MSG_FLV_LONG},
                          max_length=settings.MAX_FILENAME_LENGTH)
    ogv = forms.FileField(required=False,
                          error_messages={'max_length': MSG_OGV_LONG},
                          max_length=settings.MAX_FILENAME_LENGTH)
    webm = forms.FileField(required=False,
                           error_messages={'max_length': MSG_WEBM_LONG},
                           max_length=settings.MAX_FILENAME_LENGTH)
    thumbnail = forms.ImageField(required=False,
                                 error_messages={'max_length': MSG_IMAGE_LONG},
                                 max_length=settings.MAX_FILENAME_LENGTH)
    locale = forms.ChoiceField(
                    choices=[(LOCALES[k].external, LOCALES[k].native) for
                             k in settings.SUMO_LANGUAGES],
                    initial=settings.WIKI_DEFAULT_LANGUAGE)
    title = StrippedCharField(
        min_length=5, max_length=255,
        error_messages={'required': MSG_TITLE_REQUIRED,
                        'min_length': MSG_TITLE_SHORT,
                        'max_length': MSG_TITLE_LONG})
    description = StrippedCharField(
        max_length=10000, widget=forms.Textarea(),
        error_messages={'required': MSG_DESCRIPTION_REQUIRED,
                        'max_length': MSG_DESCRIPTION_LONG})

    def clean(self):
        """Ensure one of the supported file formats has been uploaded"""
        c = super(VideoForm, self).clean()
        if not ('webm' in c and c['webm'] or
                'ogv' in c and c['ogv'] or
                'flv' in c and c['flv']):
            raise ValidationError(MSG_VID_REQUIRED)
        clean_draft(self, c)
        return self.cleaned_data

    def save(self, update_user=None, **kwargs):
        return save_form(self, update_user, **kwargs)

    class Meta:
        model = Video
        fields = ('webm', 'ogv', 'flv', 'thumbnail', 'locale',
                  'title', 'description')


def clean_draft(form, cleaned_data):
    """Drafts reserve a special title."""
    c = cleaned_data
    if 'title' in c and c['title'].startswith(DRAFT_TITLE_PREFIX):
        raise ValidationError(MSG_TITLE_DRAFT)
    return c


def save_form(form, update_user=None, **kwargs):
    """Save a media form, add user to updated_by."""
    obj = super(form.__class__, form).save(commit=False, **kwargs)
    if update_user:
        obj.updated_by = update_user
    obj.save()
    return obj
