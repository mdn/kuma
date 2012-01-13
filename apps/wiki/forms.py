import json
import re

from django import forms
from django.utils.encoding import smart_str
from django.forms.widgets import CheckboxSelectMultiple

from tower import ugettext_lazy as _lazy
from tower import ugettext as _

from sumo.form_fields import StrippedCharField
from tags import forms as tag_forms

import wiki.content
from wiki.models import (Document, Revision, FirefoxVersion, OperatingSystem,
                     FIREFOX_VERSIONS, OPERATING_SYSTEMS, SIGNIFICANCES,
                     GROUPED_FIREFOX_VERSIONS, GROUPED_OPERATING_SYSTEMS,
                     CATEGORIES, REVIEW_FLAG_TAGS, RESERVED_SLUGS)


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
TITLE_COLLIDES = _lazy(u'Another document with this title already exists.')
SLUG_COLLIDES = _lazy(u'Another document with this slug already exists.')
OTHER_COLLIDES = _lazy(u'Another document with this metadata already exists.')

MIDAIR_COLLISION = _lazy(u'This document was modified while you were editing it.')


class DocumentForm(forms.ModelForm):
    """Form to create/edit a document."""
    def __init__(self, *args, **kwargs):
        can_create_tags = kwargs.pop('can_create_tags', False)

        super(DocumentForm, self).__init__(*args, **kwargs)

        # Set up tags field, which is instantiated deep within taggit:
        tags_field = self.fields['tags']
        tags_field.widget.can_create_tags = can_create_tags

    title = StrippedCharField(min_length=5, max_length=255,
                              widget=forms.TextInput(attrs={'placeholder':TITLE_PLACEHOLDER}),
                              label=_lazy(u'Title:'),
                              help_text=_lazy(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=2, max_length=255,
                             required=False,
                             widget=forms.HiddenInput(),
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

    is_localizable = forms.BooleanField(
                                initial=True,
                                label=_lazy(u'Allow translations:'),
                                required=False)

    category = forms.ChoiceField(choices=CATEGORIES,
                                 initial=10,
                                 # Required for non-translations, which is
                                 # enforced in Document.clean().
                                 required=False,
                                 label=_lazy(u'Category:'),
                                 help_text=_lazy(u'Type of article'),
                                 widget=forms.HiddenInput())

    tags = tag_forms.TagField(required=False, label=_lazy(u'Topics:'),
                              help_text=_lazy(
                                u'Popular articles in each topic '
                                'are displayed on the front page'))

    locale = forms.CharField(widget=forms.HiddenInput())

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if slug == '':
            # Default to the title, if missing.
            slug = self.cleaned_data['title']
        # "?" disallowed in slugs altogether
        if '?' in slug:
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
        fields = ('title', 'slug', 'category', 'is_localizable', 'tags',
                  'locale')

    def save(self, parent_doc, **kwargs):
        """Persist the Document form, and return the saved Document."""
        doc = super(DocumentForm, self).save(commit=False, **kwargs)
        doc.parent = parent_doc
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

    title = StrippedCharField(min_length=5, max_length=255,
                              required=False,
                              widget=forms.TextInput(attrs={'placeholder':TITLE_PLACEHOLDER}),
                              label=_lazy(u'Title:'),
                              help_text=_lazy(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=2, max_length=255,
                             required=False,
                             widget=forms.TextInput(),
                             label=_lazy(u'Slug:'),
                             help_text=_lazy(u'Article URL'),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})
    
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
        'oses': [(smart_str(c[0][0]), [(o.slug, smart_str(o.name)) for
                                    o in c[1]]) for
                 c in GROUPED_OPERATING_SYSTEMS],
        'versions': [(smart_str(c[0][0]), [(v.slug, smart_str(v.name)) for
                                        v in c[1] if v.show_in_ui]) for
                     c in GROUPED_FIREFOX_VERSIONS]}

    content = StrippedCharField(
                min_length=5, max_length=100000,
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

    current_rev = forms.CharField(required=False,
                                  widget=forms.HiddenInput())

    class Meta(object):
        model = Revision
        fields = ('title', 'slug', 'keywords', 'summary', 'content', 'comment',
                  'based_on')

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
            tool = wiki.content.parse(content)
            tool.injectSectionIDs()
            if self.section_id:
                tool.extractSection(self.section_id)
            self.initial['content'] = tool.serialize()

            self.initial['review_tags'] = [x.name 
                for x in self.instance.review_tags.all()]

    def _clean_collidable(self, name):
        value = self.cleaned_data[name]
        
        if self.is_iframe_target:
            # Since these collidables can change the URL of the page, changes
            # to them are ignored for an iframe submission
            return getattr(self.instance.document, name)

        error_message = {'title': TITLE_COLLIDES, 
                         'slug': SLUG_COLLIDES}.get(name, OTHER_COLLIDES)
        try:
            existing_doc = Document.uncached.get(locale=self.instance.document.locale,
                                                 **{name: value} )
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

    def clean_title(self):
        return self._clean_collidable('title')

    def clean_slug(self):
        return self._clean_collidable('slug')

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

                if self.section_id and self.instance and self.instance.document:
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
        new_rev.review_tags.set(*self.cleaned_data['review_tags'])
        return new_rev


class ReviewForm(forms.Form):
    comment = StrippedCharField(max_length=255, widget=forms.Textarea(),
                                required=False, label=_lazy(u'Comment:'),
                                error_messages={'max_length': COMMENT_LONG})

    significance = forms.ChoiceField(
                    label=_lazy(u'Significance:'),
                    choices=SIGNIFICANCES, initial=SIGNIFICANCES[0][0],
                    required=False, widget=forms.RadioSelect())
