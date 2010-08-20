from django import forms

from tower import ugettext_lazy as _lazy

from sumo.form_fields import StrippedCharField
from .models import Document, Revision


TITLE_REQUIRED = _lazy(u'Please provide a title.')
TITLE_SHORT = _lazy(u'Your title is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
TITLE_LONG = _lazy(u'Please keep the length of your title to %(limit_value)s characters or less. It is currently %(show_value)s characters.')
SUMMARY_REQUIRED = _lazy(u'Please provide a summary.')
SUMMARY_SHORT = _lazy(u'The summary is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
SUMMARY_LONG = _lazy(u'Please keep the length of the summary to %(limit_value)s characters or less. It is currently %(show_value)s characters.')
CONTENT_REQUIRED = _lazy(u'Please provide content.')
CONTENT_SHORT = _lazy(u'The content is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
CONTENT_LONG = _lazy(u'Please keep the length of the content to %(limit_value)s characters or less. It is currently %(show_value)s characters.')


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""
    title = StrippedCharField(min_length=5, max_length=255,
                              widget=forms.TextInput(),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})

    class Meta:
        model = Document
        fields = ('title', 'category', 'tags')


class RevisionForm(forms.ModelForm):
    """Form to create new revisions."""
    summary = StrippedCharField(
                min_length=5, max_length=1000, widget=forms.Textarea(),
                error_messages={'required': SUMMARY_REQUIRED,
                                'min_length': SUMMARY_SHORT,
                                'max_length': SUMMARY_LONG})
    content = StrippedCharField(
                min_length=5, max_length=10000, widget=forms.Textarea(),
                error_messages={'required': CONTENT_REQUIRED,
                                'min_length': CONTENT_SHORT,
                                'max_length': CONTENT_LONG})

    class Meta:
        model = Revision
        fields = ('summary', 'content', 'keywords', 'significance')
