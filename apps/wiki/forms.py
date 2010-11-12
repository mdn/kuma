import json

from django import forms
from django.utils.encoding import smart_str

from tower import ugettext_lazy as _lazy
from tower import ugettext as _

from sumo.form_fields import StrippedCharField
from wiki.models import (Document, Revision, FirefoxVersion, OperatingSystem,
                     FIREFOX_VERSIONS, OPERATING_SYSTEMS, SIGNIFICANCES,
                     GROUPED_FIREFOX_VERSIONS, GROUPED_OPERATING_SYSTEMS,
                     CATEGORIES)


KEYWORDS_HELP_TEXT = _lazy(u'Keywords are used to improve searches.')

TITLE_REQUIRED = _lazy(u'Please provide a title.')
TITLE_SHORT = _lazy(u'The title is too short (%(show_value)s characters). '
                    u'It must be at least %(limit_value)s characters.')
TITLE_LONG = _lazy(u'Please keep the length of the title to %(limit_value)s '
                   u'characters or less. It is currently %(show_value)s '
                   u'characters.')
SLUG_REQUIRED = _lazy('Please provide a slug.')
SLUG_SHORT = _lazy(u'The slug is too short (%(show_value)s characters). '
                   u'It must be at least %(limit_value)s characters.')
SLUG_LONG = _lazy(u'Please keep the length of the slug to %(limit_value)s '
                  u'characters or less. It is currently %(show_value)s '
                  u'characters.')
SUMMARY_REQUIRED = _lazy(u'Please provide a summary.')
SUMMARY_SHORT = _lazy(u'The summary is too short (%(show_value)s characters). '
                      u'It must be at least %(limit_value)s characters.')
SUMMARY_LONG = _lazy(u'Please keep the length of the summary to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')
CONTENT_REQUIRED = _lazy('Please provide content.')
CONTENT_SHORT = _lazy(u'The content is too short (%(show_value)s characters). '
                      u'It must be at least %(limit_value)s characters.')
CONTENT_LONG = _lazy(u'Please keep the length of the content to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')
COMMENT_LONG = _lazy(u'Please keep the length of the comment to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""
    title = StrippedCharField(min_length=5, max_length=255,
                              widget=forms.TextInput(),
                              label=_('Title of article:'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=5, max_length=255,
                             widget=forms.TextInput(),
                             label=_('Article URL:'),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})

    firefox_versions = forms.MultipleChoiceField(
                                label=_('Firefox version:'),
                                choices=[(v.id, v.long) for v in
                                         FIREFOX_VERSIONS],
                                initial=[v.id for v in FIREFOX_VERSIONS],
                                required=False,
                                widget=forms.CheckboxSelectMultiple())

    operating_systems = forms.MultipleChoiceField(
                                label=_('Operating systems:'),
                                choices=[(o.id, o.name) for o in
                                         OPERATING_SYSTEMS],
                                initial=[o.id for o in OPERATING_SYSTEMS],
                                required=False,
                                widget=forms.CheckboxSelectMultiple())

    is_localizable = forms.BooleanField(
                                initial=True,
                                label=_('Allow translations:'),
                                required=False)

    category = forms.ChoiceField(choices=CATEGORIES,
                                 label=_('Type of article:'))

    locale = forms.CharField(widget=forms.HiddenInput())

    def clean_firefox_versions(self):
        data = self.cleaned_data['firefox_versions']
        return [FirefoxVersion(item_id=int(x)) for x in data]

    def clean_operating_systems(self):
        data = self.cleaned_data['operating_systems']
        return [OperatingSystem(item_id=int(x)) for x in data]

    class Meta:
        model = Document
        fields = ('title', 'slug', 'category', 'is_localizable', 'tags',
                  'locale')

    def save(self, parent_doc, **kwargs):
        """Persist the Document form, and return the saved Document."""
        doc = super(DocumentForm, self).save(commit=False, **kwargs)
        doc.parent = parent_doc
        doc.save()
        self.save_m2m()  # not strictly necessary since we didn't change
                         # any m2m data since we instantiated the doc

        # TODO: Use the tagging widget instead of this. Right now, anybody who
        # can edit this field can create new tags; this is supposed to be a
        # curated vocab.
        tags = self.cleaned_data['tags']
        doc.tags.exclude(name__in=tags).delete()
        doc.tags.add(*tags)

        ffv = self.cleaned_data['firefox_versions']
        doc.firefox_versions.all().delete()
        doc.firefox_versions = ffv
        os = self.cleaned_data['operating_systems']
        doc.operating_systems.all().delete()
        doc.operating_systems = os

        return doc


class RevisionForm(forms.ModelForm):
    """Form to create new revisions."""
    keywords = StrippedCharField(required=False,
                                 label=_('Affects search results'),
                                 help_text=KEYWORDS_HELP_TEXT)

    summary = StrippedCharField(
                min_length=5, max_length=1000, widget=forms.Textarea(),
                label=_lazy('Only displayed on search results page'),
                error_messages={'required': SUMMARY_REQUIRED,
                                'min_length': SUMMARY_SHORT,
                                'max_length': SUMMARY_LONG})

    showfor_data = {
        'oses': [(smart_str(c[0][0]), [(o.slug, smart_str(o.name)) for
                                    o in c[1]]) for
                 c in GROUPED_OPERATING_SYSTEMS],
        'versions': [(smart_str(c[0][0]), [(v.slug, smart_str(v.name)) for
                                        v in c[1] if v.show_in_ui]) for
                     c in GROUPED_FIREFOX_VERSIONS]}
    content = StrippedCharField(
                min_length=5, max_length=100000,
                widget=forms.Textarea(attrs={'data-showfor':
                                             json.dumps(showfor_data)}),
                error_messages={'required': CONTENT_REQUIRED,
                                'min_length': CONTENT_SHORT,
                                'max_length': CONTENT_LONG})

    comment = StrippedCharField(required=False)

    class Meta(object):
        model = Revision
        fields = ('keywords', 'summary', 'content', 'comment', 'based_on')

    def __init__(self, *args, **kwargs):
        super(RevisionForm, self).__init__(*args, **kwargs)
        self.fields['based_on'].widget = forms.HiddenInput()

    def save(self, creator, document, **kwargs):
        """Persist me, and return the saved Revision.

        Take several other necessary pieces of data that aren't from the
        form.

        """
        # Throws a TypeError if somebody passes in a commit kwarg:
        new_rev = super(RevisionForm, self).save(commit=False, **kwargs)

        new_rev.document = document
        new_rev.creator = creator
        new_rev.save()
        return new_rev


class ReviewForm(forms.Form):
    comment = StrippedCharField(max_length=255, widget=forms.Textarea(),
                                required=False,
                                error_messages={'max_length': COMMENT_LONG})

    significance = forms.ChoiceField(
                    choices=SIGNIFICANCES, initial=SIGNIFICANCES[0][0],
                    required=False, widget=forms.RadioSelect())
