from django import forms

from tower import ugettext_lazy as _lazy
from tower import ugettext as _

from sumo.form_fields import StrippedCharField
from .models import (Document, Revision, FirefoxVersion, OperatingSystem,
                     FIREFOX_VERSIONS, OPERATING_SYSTEMS, SIGNIFICANCES)


KEYWORDS_HELP_TEXT = _lazy(u'Keywords are used to improve searches.')

TITLE_REQUIRED = _lazy(u'Please provide a title.')
TITLE_SHORT = _lazy(u'Your title is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
TITLE_LONG = _lazy(u'Please keep the length of your title to %(limit_value)s characters or less. It is currently %(show_value)s characters.')
SLUG_REQUIRED = _lazy(u'Please provide a slug.')
SLUG_SHORT = _lazy(u'Your slug is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
SLUG_LONG = _lazy(u'Please keep the length of your slug to %(limit_value)s characters or less. It is currently %(show_value)s characters.')
SUMMARY_REQUIRED = _lazy(u'Please provide a summary.')
SUMMARY_SHORT = _lazy(u'The summary is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
SUMMARY_LONG = _lazy(u'Please keep the length of the summary to %(limit_value)s characters or less. It is currently %(show_value)s characters.')
CONTENT_REQUIRED = _lazy(u'Please provide content.')
CONTENT_SHORT = _lazy(u'The content is too short (%(show_value)s characters). It must be at least %(limit_value)s characters.')
CONTENT_LONG = _lazy(u'Please keep the length of the content to %(limit_value)s characters or less. It is currently %(show_value)s characters.')
COMMENT_LONG = _lazy(u'Please keep the length of the comment to %(limit_value)s characters or less. It is currently %(show_value)s characters.')


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""
    title = StrippedCharField(min_length=5, max_length=255,
                              widget=forms.TextInput(),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=5, max_length=255,
                             widget=forms.TextInput(),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})

    firefox_versions = forms.MultipleChoiceField(
                                label=_('Firefox Version'),
                                choices=FIREFOX_VERSIONS, required=False,
                                widget=forms.CheckboxSelectMultiple())

    operating_systems = forms.MultipleChoiceField(
                                label=_('Operating Systems'),
                                choices=OPERATING_SYSTEMS, required=False,
                                widget=forms.CheckboxSelectMultiple())

    def clean_firefox_versions(self):
        data = self.cleaned_data['firefox_versions']
        return [FirefoxVersion(item_id=int(x)) for x in data]

    def clean_operating_systems(self):
        data = self.cleaned_data['operating_systems']
        return [OperatingSystem(item_id=int(x)) for x in data]

    class Meta:
        model = Document
        fields = ('title', 'slug', 'category', 'tags')


class RevisionForm(forms.ModelForm):
    """Form to create new revisions."""
    keywords = StrippedCharField(required=False, help_text=KEYWORDS_HELP_TEXT)

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
        fields = ('keywords', 'summary', 'content', 'significance')


class ReviewForm(forms.Form):
    comment = StrippedCharField(max_length=255, widget=forms.Textarea(),
                                required=False,
                                error_messages={'max_length': COMMENT_LONG})

    significance = forms.ChoiceField(
                    choices=SIGNIFICANCES, required=False,
                    widget=forms.RadioSelect())
