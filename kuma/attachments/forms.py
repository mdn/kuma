import magic
from django import forms
from django.core.validators import EMPTY_VALUES
from django.utils.translation import gettext_lazy as _

from .models import AttachmentRevision


MIME_TYPE_INVALID = _("Files of this type are not permitted.")


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
        fields = ("file", "title", "description", "comment")

    def __init__(self, *args, **kwargs):
        self.allow_svg_uploads = kwargs.pop("allow_svg_uploads", False)
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
        submitted_mime_type = cleaned_data.get("mime_type")

        if submitted_mime_type in nulls and "file" in cleaned_data:
            self.mime_type = self.mime_type_from_file(cleaned_data["file"])
            if self.mime_type.startswith("image/svg") and self.allow_svg_uploads:
                # The `magic.Magic()` will, for unknown reasons, sometimes
                # think an SVG image's mime type is `image/svg` which not
                # a valid mime type actually.
                # See https://www.iana.org/assignments/media-types/media-types.xhtml#image
                # So correct that.
                if self.mime_type == "image/svg":
                    self.mime_type = "image/svg+xml"

        return cleaned_data

    def save(self, *args, **kwargs):
        revision = super(AttachmentRevisionForm, self).save(*args, **kwargs)
        if self.mime_type is not None:
            revision.mime_type = self.mime_type
        return revision

    def mime_type_from_file(self, file):
        m_mime = magic.Magic(mime=True)
        mime_type = m_mime.from_buffer(file.read(1024)).split(";")[0]
        file.seek(0)
        return mime_type


class AdminAttachmentRevisionForm(AttachmentRevisionForm):
    class Meta(AttachmentRevisionForm.Meta):
        fields = [
            "attachment",
            "file",
            "title",
            "mime_type",
            "description",
            "is_approved",
        ]
