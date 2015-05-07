import magic
from tower import ugettext_lazy as _lazy

from django import forms

from constance import config

from .models import AttachmentRevision


MIME_TYPE_INVALID = _lazy(u'Files of this type are not permitted.')


class AttachmentRevisionForm(forms.ModelForm):
    # Unlike the DocumentForm/RevisionForm split, we have only one
    # form for file attachments. The handling view will determine if
    # this is a new revision of an existing file, or the first version
    # of a new file.
    #
    # As a result of this, calling save(commit=True) is off-limits.
    class Meta:
        model = AttachmentRevision
        fields = ('file', 'title', 'description', 'comment')

    def clean_file(self):
        uploaded_file = self.cleaned_data['file']
        m_mime = magic.Magic(mime=True)
        mime_type = m_mime.from_buffer(uploaded_file.read(1024)).split(';')[0]
        uploaded_file.seek(0)

        if mime_type not in \
                config.WIKI_ATTACHMENT_ALLOWED_TYPES.split():
            raise forms.ValidationError(MIME_TYPE_INVALID)
        return self.cleaned_data['file']

    def save(self, commit=True):
        if commit:
            raise NotImplementedError
        rev = super(AttachmentRevisionForm, self).save(commit=False)

        uploaded_file = self.cleaned_data['file']
        m_mime = magic.Magic(mime=True)
        mime_type = m_mime.from_buffer(uploaded_file.read(1024)).split(';')[0]
        rev.slug = uploaded_file.name

        # TODO: we probably want a "manually fix the mime-type"
        # ability in the admin.
        if mime_type is None:
            mime_type = 'application/octet-stream'
        rev.mime_type = mime_type

        return rev
