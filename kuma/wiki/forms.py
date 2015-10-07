import logging

import waffle
from taggit.utils import parse_tags
from tower import ugettext as _
from tower import ugettext_lazy as _lazy

from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.forms.widgets import CheckboxSelectMultiple
from django.utils.text import get_text_list

import kuma.wiki.content
from kuma.contentflagging.forms import ContentFlagForm
from kuma.core.form_fields import StrippedCharField

from .constants import (DOCUMENT_PATH_RE, INVALID_DOC_SLUG_CHARS_RE,
                        INVALID_REV_SLUG_CHARS_RE, LOCALIZATION_FLAG_TAGS,
                        RESERVED_SLUGS_RES, REVIEW_FLAG_TAGS,
                        SLUG_CLEANSING_RE)
from .events import EditDocumentEvent
from .models import (Document, DocumentTag, Revision, RevisionIP,
                     valid_slug_parent)
from .tasks import send_first_edit_email


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
MOVE_REQUIRED = _lazy(u"Changing this document's slug requires "
                      u"moving it and its children.")
TAG_DUPE = _lazy(u'There is another tag matching this tag that only differs '
                 u'by case. Please use these tag(s) instead: %(tag)s.')


log = logging.getLogger('kuma.wiki.forms')


class DocumentForm(forms.ModelForm):
    """
    Used for managing the wiki document data model that houses general
    data of a wiki page.
    """
    title = StrippedCharField(min_length=1,
                              max_length=255,
                              widget=forms.TextInput(
                                  attrs={'placeholder': TITLE_PLACEHOLDER}),
                              label=_lazy(u'Title:'),
                              help_text=_lazy(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})

    slug = StrippedCharField(min_length=1,
                             max_length=255,
                             widget=forms.TextInput(),
                             label=_lazy(u'Slug:'),
                             help_text=_lazy(u'Article URL'),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})

    category = forms.ChoiceField(choices=Document.CATEGORIES,
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

    class Meta:
        model = Document
        fields = ('title', 'slug', 'category', 'locale')

    def __init__(self, *args, **kwargs):
        # when creating a new document with a parent, this will be set
        self.parent_slug = kwargs.pop('parent_slug', None)
        super(DocumentForm, self).__init__(*args, **kwargs)

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        if slug == '':
            # Default to the title, if missing.
            slug = self.cleaned_data['title']
        elif self.parent_slug:
            # Prepend parent slug if given from view
            slug = self.parent_slug + '/' + slug
        # check both for disallowed characters and match for the allowed
        if (INVALID_DOC_SLUG_CHARS_RE.search(slug) or
                not DOCUMENT_PATH_RE.search(slug)):
            raise forms.ValidationError(SLUG_INVALID)
        # Guard against slugs that match urlpatterns
        for pattern in RESERVED_SLUGS_RES:
            if pattern.match(slug):
                raise forms.ValidationError(SLUG_INVALID)
        return slug

    def save(self, parent=None, *args, **kwargs):
        """Persist the Document form, and return the saved Document."""
        doc = super(DocumentForm, self).save(commit=False, *args, **kwargs)
        doc.parent = parent
        if 'parent_topic' in self.cleaned_data:
            doc.parent_topic = self.cleaned_data['parent_topic']
        doc.save()
        # not strictly necessary since we didn't change
        # any m2m data since we instantiated the doc
        self.save_m2m()
        return doc


class RevisionForm(forms.ModelForm):
    """
    Form to create new revisions.
    """
    title = StrippedCharField(min_length=1,
                              max_length=255,
                              required=False,
                              widget=forms.TextInput(
                                  attrs={'placeholder': TITLE_PLACEHOLDER}),
                              label=_lazy(u'Title:'),
                              help_text=_lazy(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=1,
                             max_length=255,
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

    summary = StrippedCharField(
        required=False,
        min_length=5,
        max_length=1000,
        widget=forms.Textarea(),
        label=_lazy(u'Search result summary:'),
        help_text=_lazy(u'Only displayed on search results page'),
        error_messages={'required': SUMMARY_REQUIRED,
                        'min_length': SUMMARY_SHORT,
                        'max_length': SUMMARY_LONG})

    content = StrippedCharField(
        min_length=5,
        max_length=300000,
        label=_lazy(u'Content:'),
        widget=forms.Textarea(),
        error_messages={'required': CONTENT_REQUIRED,
                        'min_length': CONTENT_SHORT,
                        'max_length': CONTENT_LONG})

    comment = StrippedCharField(required=False, label=_lazy(u'Comment:'))

    review_tags = forms.MultipleChoiceField(
        label=_("Tag this revision for review?"),
        widget=CheckboxSelectMultiple,
        required=False,
        choices=REVIEW_FLAG_TAGS)

    localization_tags = forms.MultipleChoiceField(
        label=_("Tag this revision for localization?"),
        widget=CheckboxSelectMultiple,
        required=False,
        choices=LOCALIZATION_FLAG_TAGS)

    current_rev = forms.CharField(required=False,
                                  widget=forms.HiddenInput())

    class Meta(object):
        model = Revision
        fields = ('title', 'slug', 'tags', 'keywords', 'summary', 'content',
                  'comment', 'based_on', 'toc_depth',
                  'render_max_age')

    def __init__(self, *args, **kwargs):
        self.section_id = kwargs.pop('section_id', None)
        self.is_iframe_target = kwargs.pop('is_iframe_target', None)

        # when creating a new document with a parent, this will be set
        self.parent_slug = kwargs.pop('parent_slug', None)

        super(RevisionForm, self).__init__(*args, **kwargs)

        self.fields['based_on'].widget = forms.HiddenInput()

        if self.instance and self.instance.pk:
            # Ensure both title and slug are populated from parent document,
            # if last revision didn't have them
            if not self.instance.title:
                self.initial['title'] = self.instance.document.title
            if not self.instance.slug:
                self.initial['slug'] = self.instance.document.slug

            content = self.instance.content
            if not self.instance.document.is_template:
                parsed_content = kuma.wiki.content.parse(content)
                parsed_content.injectSectionIDs()
                if self.section_id:
                    parsed_content.extractSection(self.section_id)
                parsed_content.filterEditorSafety()
                content = parsed_content.serialize()
            self.initial['content'] = content

            self.initial['review_tags'] = list(self.instance.review_tags
                                                            .values_list('name',
                                                                         flat=True))
            self.initial['localization_tags'] = list(self.instance
                                                         .localization_tags
                                                         .values_list('name',
                                                                      flat=True))

        if self.section_id:
            self.fields['toc_depth'].required = False

    def clean_slug(self):
        # Since this form can change the URL of the page on which the editing
        # happens, changes to the slug are ignored for an iframe submissions
        if self.is_iframe_target:
            return self.instance.document.slug

        # Get the cleaned slug
        slug = self.cleaned_data['slug']

        # first check if the given slug doesn't contain slashes and other
        # characters not allowed in a revision slug component (without parent)
        if slug and INVALID_REV_SLUG_CHARS_RE.search(slug):
            raise forms.ValidationError(SLUG_INVALID)

        # edits can come in without a slug, so default to the current doc slug
        if not slug:
            try:
                slug = self.instance.slug = self.instance.document.slug
            except ObjectDoesNotExist:
                pass

        # then if there is a parent document we prefix the slug with its slug
        if self.parent_slug:
            slug = u'/'.join([self.parent_slug, slug])

        try:
            doc = Document.objects.get(locale=self.instance.document.locale,
                                       slug=slug)
            if self.instance and self.instance.document:
                if (not doc.get_redirect_url() and
                        doc.pk != self.instance.document.pk):
                    # There's another document with this value,
                    # and we're not a revision of it.
                    raise forms.ValidationError(SLUG_COLLIDES)
            else:
                # This document-and-revision doesn't exist yet, so there
                # shouldn't be any collisions at all.
                raise forms.ValidationError(SLUG_COLLIDES)

        except Document.DoesNotExist:
            # No existing document for this value, so we're good here.
            pass

        return slug

    def clean_tags(self):
        """
        Validate the tags ensuring we have no case-sensitive duplicates.
        """
        tags = self.cleaned_data['tags']
        dupe_tags = []

        if tags:
            for tag in parse_tags(tags):
                # Note: The exact match query doesn't work correctly with
                # MySQL with regards to case-sensitivity. If we move to
                # Postgresql in the future this code may need to change.
                doc_tag = (DocumentTag.objects.filter(name__exact=tag)
                                              .values_list('name', flat=True))

                if doc_tag:
                    if doc_tag[0] != tag and doc_tag[0].lower() == tag.lower():
                        dupe_tags.append(doc_tag[0])

                # Write a log we can grep to help find pre-existing duplicate
                # document tags for cleanup.
                if len(doc_tag) > 1:
                    log.warn('Found duplicate document tags: %s' % doc_tag)

            if dupe_tags:
                raise forms.ValidationError(
                    TAG_DUPE % {'tag': get_text_list(dupe_tags)})

        return tags

    def clean_content(self):
        """
        Validate the content, performing any section editing if necessary
        """
        content = self.cleaned_data['content']

        # If we're editing a section, we need to replace the section content
        # from the current revision.
        if self.section_id and self.instance and self.instance.document:
            # Make sure we start with content form the latest revision.
            full_content = self.instance.document.current_revision.content
            # Replace the section content with the form content.
            parsed_content = kuma.wiki.content.parse(full_content)
            parsed_content.replaceSection(self.section_id, content)
            content = parsed_content.serialize()

        return content

    def clean_current_rev(self):
        """
        If a current revision is supplied in the form, compare it against
        what the document claims is the current revision. If there's a
        difference, then an edit has occurred since the form was constructed
        and we treat it as a mid-air collision.
        """
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
                    orig_ct = (Revision.objects
                                       .get(pk=current_rev)
                                       .get_section_content(self.section_id))
                    curr_ct = (self.instance
                                   .document.current_revision
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

    def save(self, request, document, **kwargs):
        """
        Persists the revision and returns it.
        Takes the view request and document of the revision.
        Does some specific things when the revision is fully saved.
        """
        # have to check for first edit before we save
        is_first_edit = request.user.wiki_revisions().count() == 0

        # Making sure we don't commit the saving right away since we
        # want to do other things here.
        kwargs['commit'] = False

        if self.section_id and self.instance and self.instance.document:
            # The logic to save a section is slightly different and may
            # need to evolve over time; a section edit doesn't submit
            # all the fields, and we need to account for that when we
            # construct the new Revision.
            old_rev = Document.objects.get(pk=self.instance.document.id).current_revision
            new_rev = super(RevisionForm, self).save(**kwargs)
            new_rev.document = document
            new_rev.creator = request.user
            new_rev.toc_depth = old_rev.toc_depth
            new_rev.save()
            new_rev.review_tags.set(*list(old_rev.review_tags
                                                 .values_list('name', flat=True)))

        else:
            new_rev = super(RevisionForm, self).save(**kwargs)
            new_rev.document = document
            new_rev.creator = request.user
            new_rev.toc_depth = self.cleaned_data['toc_depth']
            new_rev.save()
            new_rev.review_tags.set(*self.cleaned_data['review_tags'])
            new_rev.localization_tags.set(*self.cleaned_data['localization_tags'])

            # when enabled store the user's IP address
            if waffle.switch_is_active('store_revision_ips'):
                ip = request.META.get('REMOTE_ADDR')
                RevisionIP.objects.create(revision=new_rev, ip=ip)

            # send first edit emails
            if is_first_edit:
                send_first_edit_email.delay(new_rev.pk)

            # schedule a document rendering
            document.schedule_rendering('max-age=0')

            # schedule event notifications
            EditDocumentEvent(new_rev).fire(exclude=new_rev.creator)

        return new_rev


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
    locale = StrippedCharField(min_length=2, max_length=5,
                               widget=forms.HiddenInput())

    def clean_slug(self):
        slug = self.cleaned_data['slug']
        # We only want the slug here; inputting a full URL would lead
        # to disaster.
        if '://' in slug:
            raise forms.ValidationError('Please enter only the slug to move '
                                        'to, not the full URL.')

        # Removes leading slash and {locale/docs/} if necessary
        # IMPORTANT: This exact same regex is used on the client side, so
        # update both if doing so
        slug = SLUG_CLEANSING_RE.sub('', slug)

        # Remove the trailing slash if one is present, because it
        # will screw up the page move, which doesn't expect one.
        return slug.rstrip('/')

    def clean(self):
        cleaned_data = super(TreeMoveForm, self).clean()
        if set(['slug', 'locale']).issubset(cleaned_data):
            slug, locale = cleaned_data['slug'], cleaned_data['locale']
            try:
                valid_slug_parent(slug, locale)
            except Exception as e:
                raise forms.ValidationError(e.args[0])
        return cleaned_data


class DocumentDeletionForm(forms.Form):
    reason = forms.CharField(widget=forms.Textarea(attrs={'autofocus': 'true'}))


class DocumentContentFlagForm(ContentFlagForm):
    flag_type = forms.ChoiceField(
        choices=settings.WIKI_FLAG_REASONS,
        widget=forms.RadioSelect)
