import magic
from constance import config
from django import forms
from django.core.validators import EMPTY_VALUES
from django.utils.translation import ugettext_lazy as _

from .models import AttachmentRevision


MIME_TYPE_INVALID = _(u'Files of this type are not permitted.')


class AttachmentRevisionForm(forms.ModelForm):
    """
    Unlike the DocumentForm/RevisionForm split, we have only one
    form for file attachments. The handling view will determine if
    this is a new revision of an existing file, or the first version
    of a new file.

    As a result of this, calling save(commit=True) is off-limits.
    """
    class Meta:
        model = AttachmentRevision
        fields = ('file', 'title', 'description', 'comment')

    def __init__(self, *args, **kwargs):
        super(AttachmentRevisionForm, self).__init__(*args, **kwargs)
        self.mime_type = None

    def clean(self):
        """
        Check the submitted file for its MIME type in case the provided
        MIME type is missing or is the default MIME type as given in the
        model field definition.

        That allows overriding the MIME type via the admin UI.
        """
        cleaned_data = super(AttachmentRevisionForm, self).clean()
        nulls = EMPTY_VALUES + (AttachmentRevision.DEFAULT_MIME_TYPE,)
        submitted_mime_type = cleaned_data.get('mime_type')

        if (submitted_mime_type in nulls) and ('file' in cleaned_data):
            self.mime_type = self.mime_type_from_file(cleaned_data['file'])
            allowed_mime_types = config.WIKI_ATTACHMENT_ALLOWED_TYPES.split()
            if self.mime_type not in allowed_mime_types:
                raise forms.ValidationError(MIME_TYPE_INVALID, code='invalid')

        return cleaned_data

    def save(self, *args, **kwargs):
        revision = super(AttachmentRevisionForm, self).save(*args, **kwargs)
        if self.mime_type is not None:
            revision.mime_type = self.mime_type
        return revision

    def mime_type_from_file(self, file):
        m_mime = magic.Magic(mime=True)
        mime_type = m_mime.from_buffer(file.read(1024)).split(';')[0]
        file.seek(0)
        return mime_type


class AdminAttachmentRevisionForm(AttachmentRevisionForm):
    class Meta(AttachmentRevisionForm.Meta):
        fields = ['attachment', 'file', 'title', 'mime_type', 'description',
                  'is_approved']
