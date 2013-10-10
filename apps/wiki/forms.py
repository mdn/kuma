from datetime import datetime
import json
import re

from django import forms
from django.utils.encoding import smart_str
from django.forms.widgets import CheckboxSelectMultiple

from tower import ugettext_lazy as _lazy
from tower import ugettext as _

import constance.config
import magic

from sumo.form_fields import StrippedCharField

import wiki.content
from wiki.models import (Document, Revision, FirefoxVersion, OperatingSystem,
                         AttachmentRevision,
                         FIREFOX_VERSIONS, OPERATING_SYSTEMS, SIGNIFICANCES,
                         GROUPED_FIREFOX_VERSIONS, GROUPED_OPERATING_SYSTEMS,
                         CATEGORIES, REVIEW_FLAG_TAGS, RESERVED_SLUGS,
                         TOC_DEPTH_CHOICES, LOCALIZATION_FLAG_TAGS)
from wiki import SLUG_CLEANSING_REGEX


TITLE_REQUIRED = _lazy(u'Please provide a title.')
TITLE_SHORT = _lazy(u'The title is too short (%(show_value)s characters). '
                    u'It must be at least %(limit_value)s characters.')
TITLE_LONG = _lazy(u'Please keep the length of the title to %(limit_value)s '
                   u'characters or less. It is currently %(show_value)s '
                   u'characters.')
TITLE_PLACEHOLDER = _lazy(u'Name Your Article')
SLUG_REQUIRED = _lazy(u'Please provide a slug.')
SLUG_INVALID = _lazy(u'The slug provided is not valid.')
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
CONTENT_REQUIRED = _lazy(u'Please provide content.')
CONTENT_SHORT = _lazy(u'The content is too short (%(show_value)s characters). '
                      u'It must be at least %(limit_value)s characters.')
CONTENT_LONG = _lazy(u'Please keep the length of the content to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')
COMMENT_LONG = _lazy(u'Please keep the length of the comment to '
                     u'%(limit_value)s characters or less. It is currently '
                     u'%(show_value)s characters.')
SLUG_COLLIDES = _lazy(u'Another document with this slug already exists.')
OTHER_COLLIDES = _lazy(u'Another document with this metadata already exists.')

MIDAIR_COLLISION = _lazy(u'This document was modified while you were '
                         'editing it.')
MIME_TYPE_INVALID = _lazy(u'Files of this type are not permitted.')
MOVE_REQUIRED = _lazy(u"Changing this document's slug requires moving it and its children.")


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""

    title = StrippedCharField(min_length=1, max_length=255,
                              widget=forms.TextInput(
                                  attrs={'placeholder': TITLE_PLACEHOLDER}),
                              label=_lazy(u'Title:'),
                              help_text=_lazy(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=1, max_length=255,
                             widget=forms.TextInput(),
                             label=_lazy(u'Slug:'),
                             help_text=_lazy(u'Article URL'),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})

    firefox_versions = forms.MultipleChoiceField(
                                label=_lazy(u'Firefox version:'),
                                choices=[(v.id, v.long) for v in
                                         FIREFOX_VERSIONS],
                                initial=[v.id for v in
                                         GROUPED_FIREFOX_VERSIONS[0][1]],
                                required=False,
                                widget=forms.CheckboxSelectMultiple())

    operating_systems = forms.MultipleChoiceField(
                                label=_lazy(u'Operating systems:'),
                                choices=[(o.id, o.name) for o in
                                         OPERATING_SYSTEMS],
                                initial=[o.id for o in
                                         GROUPED_OPERATING_SYSTEMS[0][1]],
                                required=False,
                                widget=forms.CheckboxSelectMultiple())

    category = forms.ChoiceField(choices=CATEGORIES,
                                 initial=10,
                                 # Required for non-translations, which is
                                 # enforced in Document.clean().
                                 required=False,
                                 label=_lazy(u'Category:'),
                                 help_text=_lazy(u'Type of article'),
                                 widget=forms.HiddenInput())

    parent_topic = forms.ModelChoiceField(queryset=Document.objects.all(),
                                          required=False,
                                          label=_lazy(u'Parent:'))

    locale = forms.CharField(widget=forms.HiddenInput())

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if slug == '':
            # Default to the title, if missing.
            slug = self.cleaned_data['title']
        # "?", " ", quote disallowed in slugs altogether
        if '?' in slug or ' ' in slug or '"' in slug or "'" in slug:
            raise forms.ValidationError(SLUG_INVALID)
        # Pattern copied from urls.py
        if not re.compile(r'^[^\$]+$').match(slug):
            raise forms.ValidationError(SLUG_INVALID)
        # Guard against slugs that match urlpatterns
        for pat in RESERVED_SLUGS:
            if re.compile(pat).match(slug):
                raise forms.ValidationError(SLUG_INVALID)
        return slug

    def clean_firefox_versions(self):
        data = self.cleaned_data['firefox_versions']
        return [FirefoxVersion(item_id=int(x)) for x in data]

    def clean_operating_systems(self):
        data = self.cleaned_data['operating_systems']
        return [OperatingSystem(item_id=int(x)) for x in data]

    class Meta:
        model = Document
        fields = ('title', 'slug', 'category', 'locale')

    def save(self, parent_doc, **kwargs):
        """Persist the Document form, and return the saved Document."""
        doc = super(DocumentForm, self).save(commit=False, **kwargs)
        doc.parent = parent_doc
        if 'parent_topic' in self.cleaned_data:
            doc.parent_topic = self.cleaned_data['parent_topic']
        doc.save()
        self.save_m2m()  # not strictly necessary since we didn't change
                         # any m2m data since we instantiated the doc

        if not parent_doc:
            ffv = self.cleaned_data['firefox_versions']
            doc.firefox_versions.all().delete()
            doc.firefox_versions = ffv
            os = self.cleaned_data['operating_systems']
            doc.operating_systems.all().delete()
            doc.operating_systems = os

        return doc


class RevisionForm(forms.ModelForm):
    """Form to create new revisions."""

    title = StrippedCharField(min_length=1, max_length=255,
                              required=False,
                              widget=forms.TextInput(
                                  attrs={'placeholder': TITLE_PLACEHOLDER}),
                              label=_lazy(u'Title:'),
                              help_text=_lazy(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=1, max_length=255,
                             required=False,
                             widget=forms.TextInput(),
                             label=_lazy(u'Slug:'),
                             help_text=_lazy(u'Article URL'),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})

    tags = StrippedCharField(required=False,
                             label=_lazy(u'Tags:'))

    keywords = StrippedCharField(required=False,
                                 label=_lazy(u'Keywords:'),
                                 help_text=_lazy(u'Affects search results'))

    summary = StrippedCharField(required=False,
                min_length=5, max_length=1000, widget=forms.Textarea(),
                label=_lazy(u'Search result summary:'),
                help_text=_lazy(u'Only displayed on search results page'),
                error_messages={'required': SUMMARY_REQUIRED,
                                'min_length': SUMMARY_SHORT,
                                'max_length': SUMMARY_LONG})

    showfor_data = {
        'oses': [(unicode(c[0][0]), [(o.slug, unicode(o.name)) for
                                    o in c[1]]) for
                 c in GROUPED_OPERATING_SYSTEMS],
        'versions': [(unicode(c[0][0]), [(v.slug, unicode(v.name)) for
                                        v in c[1] if v.show_in_ui]) for
                     c in GROUPED_FIREFOX_VERSIONS]}

    content = StrippedCharField(
                min_length=5, max_length=300000,
                label=_lazy(u'Content:'),
                widget=forms.Textarea(attrs={'data-showfor':
                                             json.dumps(showfor_data)}),
                error_messages={'required': CONTENT_REQUIRED,
                                'min_length': CONTENT_SHORT,
                                'max_length': CONTENT_LONG})

    comment = StrippedCharField(required=False, label=_lazy(u'Comment:'))

    review_tags = forms.MultipleChoiceField(
        label=_("Tag this revision for review?"),
        widget=CheckboxSelectMultiple, required=False,
        choices=REVIEW_FLAG_TAGS)

    localization_tags = forms.MultipleChoiceField(
        label=_("Tag this revision for localization?"),
        widget=CheckboxSelectMultiple, required=False,
        choices=LOCALIZATION_FLAG_TAGS)

    current_rev = forms.CharField(required=False,
                                  widget=forms.HiddenInput())

    class Meta(object):
        model = Revision
        fields = ('title', 'slug', 'tags', 'keywords', 'summary', 'content',
                  'comment', 'based_on', 'toc_depth')

    def __init__(self, *args, **kwargs):

        # Snag some optional kwargs and delete them before calling
        # super-constructor.
        for n in ('section_id', 'is_iframe_target'):
            if n not in kwargs:
                setattr(self, n, None)
            else:
                setattr(self, n, kwargs[n])
                del kwargs[n]

        super(RevisionForm, self).__init__(*args, **kwargs)
        self.fields['based_on'].widget = forms.HiddenInput()

        if self.instance and self.instance.pk:

            # Ensure both title and slug are populated from parent document, if
            # last revision didn't have them
            if not self.instance.title:
                self.initial['title'] = self.instance.document.title
            if not self.instance.slug:
                self.initial['slug'] = self.instance.document.slug

            content = self.instance.content
            if not self.instance.document.is_template:
                tool = wiki.content.parse(content)
                tool.injectSectionIDs()
                if self.section_id:
                    tool.extractSection(self.section_id)
                tool.filterEditorSafety()
                content = tool.serialize()
            self.initial['content'] = content

            self.initial['review_tags'] = [x.name
                for x in self.instance.review_tags.all()]
            self.initial['localization_tags'] = [x.name
                for x in self.instance.localization_tags.all()]

        if self.section_id:
            self.fields['toc_depth'].required = False

    def _clean_collidable(self, name):
        value = self.cleaned_data[name]

        if self.is_iframe_target:
            # Since these collidables can change the URL of the page, changes
            # to them are ignored for an iframe submission
            return getattr(self.instance.document, name)

        error_message = {'slug': SLUG_COLLIDES}.get(name, OTHER_COLLIDES)
        try:
            existing_doc = Document.objects.get(
                    locale=self.instance.document.locale,
                    **{name: value})
            if self.instance and self.instance.document:
                if (not existing_doc.redirect_url() and
                        existing_doc.pk != self.instance.document.pk):
                    # There's another document with this value,
                    # and we're not a revision of it.
                    raise forms.ValidationError(error_message)
            else:
                # This document-and-revision doesn't exist yet, so there
                # shouldn't be any collisions at all.
                raise forms.ValidationError(error_message)

        except Document.DoesNotExist:
            # No existing document for this value, so we're good here.
            pass

        return value

    def clean_slug(self):
        # TODO: move this check somewhere else?
        # edits can come in without a slug, so default to the current doc slug
        if not self.cleaned_data['slug']:
            existing_slug = self.instance.document.slug
            self.cleaned_data['slug'] = self.instance.slug = existing_slug
        cleaned_slug = self._clean_collidable('slug')
        return cleaned_slug

    def clean_content(self):
        """Validate the content, performing any section editing if necessary"""
        content = self.cleaned_data['content']

        # If we're editing a section, we need to replace the section content
        # from the current revision.
        if self.section_id and self.instance and self.instance.document:
            # Make sure we start with content form the latest revision.
            full_content = self.instance.document.current_revision.content
            # Replace the section content with the form content.
            tool = wiki.content.parse(full_content)
            tool.replaceSection(self.section_id, content)
            content = tool.serialize()

        return content

    def clean_current_rev(self):
        """If a current revision is supplied in the form, compare it against
        what the document claims is the current revision. If there's a
        difference, then an edit has occurred since the form was constructed
        and we treat it as a mid-air collision."""
        current_rev = self.cleaned_data.get('current_rev', None)

        if not current_rev:
            # If there's no current_rev, just bail.
            return current_rev

        try:
            doc_current_rev = self.instance.document.current_revision.id
            if unicode(current_rev) != unicode(doc_current_rev):

                if (self.section_id and self.instance and
                        self.instance.document):
                    # This is a section edit. So, even though the revision has
                    # changed, it still might not be a collision if the section
                    # in particular hasn't changed.
                    orig_ct = (Revision.objects.get(pk=current_rev)
                               .get_section_content(self.section_id))
                    curr_ct = (self.instance.document.current_revision
                               .get_section_content(self.section_id))
                    if orig_ct != curr_ct:
                        # Oops. Looks like the section did actually get
                        # changed, so yeah this is a collision.
                        raise forms.ValidationError(MIDAIR_COLLISION)

                    return current_rev

                else:
                    # No section edit, so this is a flat-out collision.
                    raise forms.ValidationError(MIDAIR_COLLISION)

        except Document.DoesNotExist:
            # If there's no document yet, just bail.
            return current_rev

    def save_section(self, creator, document, **kwargs):
        """Save a section edit."""
        # This is separate because the logic is slightly different and
        # may need to evolve over time; a section edit doesn't submit
        # all the fields, and we need to account for that when we
        # construct the new Revision.

        old_rev = Document.objects.get(pk=self.instance.document.id).current_revision
        new_rev = super(RevisionForm, self).save(commit=False, **kwargs)
        new_rev.document = document
        new_rev.creator = creator
        new_rev.toc_depth = old_rev.toc_depth
        new_rev.save()
        new_rev.review_tags.set(*[t.name for t in
                                  old_rev.review_tags.all()])
        return new_rev

    def save(self, creator, document, **kwargs):
        """Persist me, and return the saved Revision.

        Take several other necessary pieces of data that aren't from the
        form.

        """
        if self.section_id and self.instance and \
           self.instance.document:
            return self.save_section(creator, document, **kwargs)
        # Throws a TypeError if somebody passes in a commit kwarg:
        new_rev = super(RevisionForm, self).save(commit=False, **kwargs)

        new_rev.document = document
        new_rev.creator = creator
        new_rev.toc_depth = self.cleaned_data['toc_depth']
        new_rev.save()
        new_rev.review_tags.set(*self.cleaned_data['review_tags'])
        new_rev.localization_tags.set(*self.cleaned_data['localization_tags'])
        return new_rev


class ReviewForm(forms.Form):
    comment = StrippedCharField(max_length=255, widget=forms.Textarea(),
                                required=False, label=_lazy(u'Comment:'),
                                error_messages={'max_length': COMMENT_LONG})

    significance = forms.ChoiceField(
                    label=_lazy(u'Significance:'),
                    choices=SIGNIFICANCES, initial=SIGNIFICANCES[0][0],
                    required=False, widget=forms.RadioSelect())


class RevisionValidationForm(RevisionForm):
    """Created primarily to disallow slashes in slugs during validation"""

    def clean_slug(self):
        is_valid = True
        original = self.cleaned_data['slug']

        # "/", "?", and " " disallowed in form input
        if (u'' == original or
            '/' in original or
            '?' in original or
            ' ' in original):
            is_valid = False
            raise forms.ValidationError(SLUG_INVALID)

        # Append parent slug data, call super, ensure still valid
        self.cleaned_data['slug'] = self.data['slug'] = (self.parent_slug +
                                                         '/' +
                                                         original)
        is_valid = (is_valid and
                    super(RevisionValidationForm, self).clean_slug())

        # Set the slug back to original
        #if not is_valid:
        self.cleaned_data['slug'] = self.data['slug'] = original

        return self.cleaned_data['slug']


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
               constance.config.WIKI_ATTACHMENT_ALLOWED_TYPES.split():
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

class TreeMoveForm(forms.Form):
    title = StrippedCharField(min_length=1, max_length=255,
                                required=False,
                                widget=forms.TextInput(
                                    attrs={'placeholder': TITLE_PLACEHOLDER}),
                                label=_lazy(u'Title:'),
                                help_text=_lazy(u'Title of article'),
                                error_messages={'required': TITLE_REQUIRED,
                                                'min_length': TITLE_SHORT,
                                                'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=1, max_length=255,
                             widget=forms.TextInput(),
                             label=_lazy(u'New slug:'),
                             help_text=_lazy(u'New article URL'),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})

    def clean_slug(self):
        # We only want the slug here; inputting a full URL would lead
        # to disaster.
        if '://' in self.cleaned_data['slug']:
            raise forms.ValidationError('Please enter only the slug to move to, not the full URL.')

        # Removes leading slash and {locale/docs/} if necessary
        # IMPORTANT: This exact same regex is used on the client side, so
        # update both if doing so
        self.cleaned_data['slug'] = re.sub(re.compile(SLUG_CLEANSING_REGEX), 
                                      '', self.cleaned_data['slug'])

        return self.cleaned_data['slug']


class DocumentDeletionForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea)
