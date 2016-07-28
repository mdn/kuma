import json
import logging
from difflib import ndiff

import waffle
from django import forms
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist
from django.forms.widgets import CheckboxSelectMultiple
from django.template.loader import render_to_string
from django.utils import translation
from django.utils.safestring import mark_safe
from django.utils.six import string_types
from django.utils.translation import ugettext_lazy as _
from django.utils.translation import ugettext
from taggit.utils import parse_tags

import kuma.wiki.content
from kuma.core.form_fields import StrippedCharField
from kuma.core.urlresolvers import reverse
from kuma.spam.akismet import AkismetError
from kuma.spam.forms import AkismetCheckFormMixin, AkismetSubmissionFormMixin

from .constants import (DOCUMENT_PATH_RE, INVALID_DOC_SLUG_CHARS_RE,
                        INVALID_REV_SLUG_CHARS_RE, LOCALIZATION_FLAG_TAGS,
                        RESERVED_SLUGS_RES, REVIEW_FLAG_TAGS,
                        SLUG_CLEANSING_RE, SPAM_EXEMPTED_FLAG,
                        SPAM_OTHER_HEADERS, SPAM_SUBMISSION_REVISION_FIELDS,
                        SPAM_TRAINING_FLAG, TEMPLATE_TITLE_PREFIX)
from .events import EditDocumentEvent
from .models import (Document, DocumentSpamAttempt, DocumentTag, Revision,
                     RevisionIP, RevisionAkismetSubmission, valid_slug_parent)
from .tasks import send_first_edit_email


TITLE_REQUIRED = _(u'Please provide a title.')
TITLE_SHORT = _(u'The title is too short (%(show_value)s characters). '
                u'It must be at least %(limit_value)s characters.')
TITLE_LONG = _(u'Please keep the length of the title to %(limit_value)s '
               u'characters or less. It is currently %(show_value)s '
               u'characters.')
TITLE_PLACEHOLDER = _(u'Name Your Article')
SLUG_REQUIRED = _(u'Please provide a slug.')
SLUG_INVALID = _(u'The slug provided is not valid.')
SLUG_SHORT = _(u'The slug is too short (%(show_value)s characters). '
               u'It must be at least %(limit_value)s characters.')
SLUG_LONG = _(u'Please keep the length of the slug to %(limit_value)s '
              u'characters or less. It is currently %(show_value)s '
              u'characters.')
SUMMARY_REQUIRED = _(u'Please provide a summary.')
SUMMARY_SHORT = _(u'The summary is too short (%(show_value)s characters). '
                  u'It must be at least %(limit_value)s characters.')
SUMMARY_LONG = _(u'Please keep the length of the summary to '
                 u'%(limit_value)s characters or less. It is currently '
                 u'%(show_value)s characters.')
CONTENT_REQUIRED = _(u'Please provide content.')
CONTENT_SHORT = _(u'The content is too short (%(show_value)s characters). '
                  u'It must be at least %(limit_value)s characters.')
CONTENT_LONG = _(u'Please keep the length of the content to '
                 u'%(limit_value)s characters or less. It is currently '
                 u'%(show_value)s characters.')
COMMENT_LONG = _(u'Please keep the length of the comment to '
                 u'%(limit_value)s characters or less. It is currently '
                 u'%(show_value)s characters.')
SLUG_COLLIDES = _(u'Another document with this slug already exists.')
OTHER_COLLIDES = _(u'Another document with this metadata already exists.')

MIDAIR_COLLISION = _(u'Publishing failed. Conflicting edit attempts detected. '
                     u'Please copy and paste your edits to a safe place and '
                     u'visit the <a href="%(url)s">revision history</a> page '
                     u'to see what was changed before making further edits.')
MOVE_REQUIRED = _(u"Changing this document's slug requires "
                  u"moving it and its children.")


log = logging.getLogger('kuma.wiki.forms')


class AkismetRevisionData(object):
    """
    Collect Akismet data at creation time or later.

    This can be used in three different scenarios:
    - A user is creating a Document
    - A user is editing a Document
    - A user created or edited a document in the past

    Derived classes customize __init__ to gather data from the relevant
    instances, and then .parameters will have the Akismet submission.
    """

    def __init__(self):
        """Initialize the parameters."""
        self.default_language = settings.WIKI_DEFAULT_LANGUAGE
        self.parameters = {
            'blog_charset': 'UTF-8',
            'comment_type': 'wiki-revision'
        }

    def akismet_lang(self, language):
        """
        Convert a Django language name to an Akismet blog_lang identifier.
        E.g.: "en-US" to "en_us"
        """
        return translation.to_locale(language).lower()

    def content_from_form(self, cleaned_data):
        """Create a combined content string from form data."""
        parts = []
        for field in SPAM_SUBMISSION_REVISION_FIELDS:
            value = cleaned_data.get(field, u'')
            if field == 'tags':
                value = self.split_tags(value)
            parts.append(value)
        return u'\n'.join(parts)

    def content_from_document(self, document):
        """Create a combined content string from a document."""
        parts = []
        current_revision = document.current_revision
        assert current_revision, "document must have a current revision."
        for field in SPAM_SUBMISSION_REVISION_FIELDS:
            if field == 'comment':
                value = u''
            elif field == 'content':
                value = current_revision.content
            elif field == 'tags':
                value = self.split_tags(current_revision.tags)
            else:
                value = getattr(document, field, '')
            parts.append(value)
        return u'\n'.join(parts)

    def content_from_revision(self, revision):
        """Create a combined content string from a Revision."""
        parts = []
        for field in SPAM_SUBMISSION_REVISION_FIELDS:
            value = getattr(revision, field) or u''
            if field == 'tags':
                value = self.split_tags(value)
            parts.append(value)
        return u'\n'.join(parts)

    def set_blog(self, request):
        """Set the blog parameter from the request object."""
        self.parameters['blog'] = request.build_absolute_uri('/')

    def set_blog_lang(self, language=None):
        """
        Set the blog_lang from a Django language name.

        If the language is not English, then report that the content may be a
        combination of the target language and untranslated English.
        """
        language = language or self.default_language
        if language == self.default_language:
            blog_lang = self.akismet_lang(language)
        else:
            blog_lang = '%s, %s' % (
                self.akismet_lang(language),
                self.akismet_lang(self.default_language))
        self.parameters['blog_lang'] = blog_lang

    def set_by_edit_request(self, request):
        """
        Add data from the content creator's request object.

        Includes:
        - The base blog address
        - The author information
        - Named HTTP headers
        - Other HTTP headers, as modeled by Akismet's Wordpress plugin:
        https://plugins.trac.wordpress.org/browser/akismet/trunk/class.akismet.php
        """
        self.set_blog(request)
        self.set_comment_author(request.user)
        meta = request.META
        self.parameters.update({
            'referrer': meta.get('HTTP_REFERER', ''),
            'user_agent': meta.get('HTTP_USER_AGENT', ''),
            'user_ip': meta.get('REMOTE_ADDR', ''),
        })

        for key, value in meta.items():
            if not isinstance(value, string_types):
                continue
            if key.startswith('HTTP_COOKIE'):
                continue
            if key.startswith('HTTP_') or key in SPAM_OTHER_HEADERS:
                self.parameters[key] = value

    def set_comment_author(self, user):
        """Set the comment author from a User object."""
        self.parameters.update({
            'comment_author': (user.fullname or user.get_full_name() or
                               user.username),
            'comment_author_email': user.email,
        })

    def set_content(self, new_content, existing_content=None):
        """Set comment_content to the new and changed non-empty lines."""
        existing_content = existing_content or u''
        diff = ndiff(existing_content.splitlines(1), new_content.splitlines(1))
        lines = []
        for line in diff:
            if line.startswith('+ '):
                diff_content = line[2:].strip()
                if diff_content:
                    lines.append(diff_content)
        self.parameters['comment_content'] = u'\n'.join(lines)

    def set_permalink(self, document, request):
        """Set the permalink for the Document."""
        doc_url = document.get_absolute_url()
        self.parameters['permalink'] = request.build_absolute_uri(doc_url)

    def split_tags(self, tag_string):
        """Turn '"Tag 2" "Tag 1"' into 'Tag 1\nTag 2'."""
        return u'\n'.join(parse_tags(tag_string))


class AkismetNewDocumentData(AkismetRevisionData):
    """Collect Akismet data for a user creating a new document."""

    def __init__(self, request, cleaned_data, language=None):
        """
        Initialize from a new document form submission by the author.

        Keyword Parameters:
        request - the Request for the author
        cleaned_data - the validated form data
        language - the language of the revision being created
        """
        super(AkismetNewDocumentData, self).__init__()
        self.set_by_edit_request(request)
        self.set_blog_lang(language)
        new_content = self.content_from_form(cleaned_data)
        self.set_content(new_content)


class AkismetNewTranslationData(AkismetRevisionData):
    """Collect Akismet data for a user creating a new translation."""

    def __init__(self, request, cleaned_data, english_document, language):
        """
        Initialize from a new translation form submission by the author.

        Keyword Parameters:
        request - the Request for the author
        cleaned_data - the validated form data
        english_document - the original English document
        language - the language of the revision being created
        """
        super(AkismetNewTranslationData, self).__init__()
        self.set_by_edit_request(request)
        self.set_blog_lang(language)
        new_content = self.content_from_form(cleaned_data)
        existing_content = self.content_from_document(english_document)
        self.set_content(new_content, existing_content)


class AkismetEditDocumentData(AkismetRevisionData):
    """Collect Akismet data for a user editing an existing document."""

    def __init__(self, request, cleaned_data, document):
        """
        Initialize from an edit page form submission by the author.

        Keyword Parameters:
        request - the Request for the author
        cleaned_data - the validated form data
        document - the document the user is editing
        """
        super(AkismetEditDocumentData, self).__init__()
        self.set_by_edit_request(request)
        self.set_blog_lang(document.locale)
        self.set_permalink(document, request)
        new_content = self.content_from_form(cleaned_data)
        existing_content = self.content_from_document(document)
        self.set_content(new_content, existing_content)


class AkismetHistoricalData(AkismetRevisionData):
    """Collect Akismet data from a historical revision."""

    def __init__(self, revision, request=None):
        """Initialize from a historical revision.

        Keyword Parameters:
        revision - the historical Revision
        request - an optional request object
        """
        assert revision.id, "Must be a saved Revision."
        assert revision.document_id, "Must be a Revision with a Document."
        super(AkismetHistoricalData, self).__init__()
        revision_ip = revision.revisionip_set.first()
        if revision_ip:
            if revision_ip.data:
                # Use captured Akismet submission
                self.parameters = json.loads(revision_ip.data)
                return
            else:
                self.parameters.update({
                    'user_ip': revision_ip.ip,
                    'user_agent': revision_ip.user_agent,
                    'referrer': revision_ip.referrer,
                })
        else:
            self.parameters.update({
                'user_ip': '0.0.0.0',
                'user_agent': '',
                'referrer': '',
            })
        document = revision.document
        self.set_blog_lang(document.locale)
        if request:
            self.set_blog(request)
            self.set_permalink(document, request)
        self.set_comment_author(revision.creator)
        new_content = self.content_from_revision(revision)
        old_revision = revision.get_previous()
        if old_revision:
            old_content = self.content_from_revision(old_revision)
        else:
            old_content = None
        self.set_content(new_content, old_content)


class DocumentForm(forms.ModelForm):
    """
    Used for managing the wiki document data model that houses general
    data of a wiki page.
    """
    title = StrippedCharField(min_length=1,
                              max_length=255,
                              widget=forms.TextInput(
                                  attrs={'placeholder': TITLE_PLACEHOLDER}),
                              label=_(u'Title:'),
                              help_text=_(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})

    slug = StrippedCharField(min_length=1,
                             max_length=255,
                             widget=forms.TextInput(),
                             label=_(u'Slug:'),
                             help_text=_(u'Article URL'),
                             error_messages={'required': SLUG_REQUIRED,
                                             'min_length': SLUG_SHORT,
                                             'max_length': SLUG_LONG})

    parent_topic = forms.ModelChoiceField(queryset=Document.objects.all(),
                                          required=False,
                                          label=_(u'Parent:'))

    locale = forms.CharField(widget=forms.HiddenInput())

    class Meta:
        model = Document
        fields = ('title', 'slug', 'locale')

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


class RevisionForm(AkismetCheckFormMixin, forms.ModelForm):
    """
    Form to create new revisions.
    """
    title = StrippedCharField(
        min_length=1,
        max_length=255,
        required=False,
        widget=forms.TextInput(attrs={'placeholder': TITLE_PLACEHOLDER}),
        label=_(u'Title:'),
        help_text=_(u'Title of article'),
        error_messages={
            'required': TITLE_REQUIRED,
            'min_length': TITLE_SHORT,
            'max_length': TITLE_LONG,
        }
    )

    slug = StrippedCharField(
        min_length=1,
        max_length=255,
        required=False,
        widget=forms.TextInput(),
        label=_(u'Slug:'),
        help_text=_(u'Article URL'),
        error_messages={
            'required': SLUG_REQUIRED,
            'min_length': SLUG_SHORT,
            'max_length': SLUG_LONG,
        }
    )

    tags = StrippedCharField(
        required=False,
        label=_(u'Tags:'),
    )

    keywords = StrippedCharField(
        required=False,
        label=_(u'Keywords:'),
        help_text=_(u'Affects search results'),
    )

    summary = StrippedCharField(
        required=False,
        min_length=5,
        max_length=1000,
        widget=forms.Textarea(),
        label=_(u'Search result summary:'),
        help_text=_(u'Only displayed on search results page'),
        error_messages={
            'required': SUMMARY_REQUIRED,
            'min_length': SUMMARY_SHORT,
            'max_length': SUMMARY_LONG
        },
    )

    content = StrippedCharField(
        min_length=5,
        max_length=300000,
        label=_(u'Content:'),
        widget=forms.Textarea(),
        error_messages={
            'required': CONTENT_REQUIRED,
            'min_length': CONTENT_SHORT,
            'max_length': CONTENT_LONG,
        }
    )

    comment = StrippedCharField(
        max_length=255,
        required=False,
        label=_(u'Comment:')
    )

    review_tags = forms.MultipleChoiceField(
        label=ugettext("Tag this revision for review?"),
        widget=CheckboxSelectMultiple,
        required=False,
        choices=REVIEW_FLAG_TAGS,
    )

    localization_tags = forms.MultipleChoiceField(
        label=ugettext("Tag this revision for localization?"),
        widget=CheckboxSelectMultiple,
        required=False,
        choices=LOCALIZATION_FLAG_TAGS,
    )

    current_rev = forms.CharField(
        required=False,
        widget=forms.HiddenInput(),
    )

    class Meta(object):
        model = Revision
        fields = ('title', 'slug', 'tags', 'keywords', 'summary', 'content',
                  'comment', 'based_on', 'toc_depth',
                  'render_max_age')

    def __init__(self, *args, **kwargs):
        self.section_id = kwargs.pop('section_id', None)
        self.is_async_submit = kwargs.pop('is_async_submit', None)

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

            self.initial['review_tags'] = list(self.instance
                                                   .review_tags
                                                   .names())
            self.initial['localization_tags'] = list(self.instance
                                                         .localization_tags
                                                         .names())

        if self.section_id:
            self.fields['toc_depth'].required = False
        self.is_template = None

    def clean_slug(self):
        # Since this form can change the URL of the page on which the editing
        # happens, changes to the slug are ignored for an iframe submissions
        if self.is_async_submit:
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

        self.is_template = slug.startswith(TEMPLATE_TITLE_PREFIX)
        return slug

    def clean_tags(self):
        """
        Validate the tags ensuring we have no case-sensitive duplicates.
        """
        tags = self.cleaned_data['tags']
        cleaned_tags = []

        if tags:
            for tag in parse_tags(tags):
                # Note: The exact match query doesn't work correctly with
                # MySQL with regards to case-sensitivity. If we move to
                # Postgresql in the future this code may need to change.
                doc_tag = (DocumentTag.objects.filter(name__exact=tag)
                                              .values_list('name', flat=True))

                # Write a log we can grep to help find pre-existing duplicate
                # document tags for cleanup.
                if len(doc_tag) > 1:
                    log.warn('Found duplicate document tags: %s' % doc_tag)

                if doc_tag:
                    if doc_tag[0] != tag and doc_tag[0].lower() == tag.lower():
                        # The tag differs only by case. Do not add a new one,
                        # add the existing one.
                        cleaned_tags.append(doc_tag[0])
                        continue

                cleaned_tags.append(tag)

        return ' '.join([u'"%s"' % t for t in cleaned_tags])

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
                        url = reverse(
                            'wiki.document_revisions',
                            kwargs={'document_path': self.instance.document.slug}
                        )
                        raise forms.ValidationError(MIDAIR_COLLISION % {'url': url})

                    return current_rev

                else:
                    # No section edit, so this is a flat-out collision.
                    url = reverse(
                        'wiki.document_revisions',
                        kwargs={'document_path': self.instance.document.slug}
                    )
                    raise forms.ValidationError(MIDAIR_COLLISION % {'url': url})

        except Document.DoesNotExist:
            # If there's no document yet, just bail.
            return current_rev

    def akismet_enabled(self):
        """
        Adds two ways that Akismet checks could be disabled:
        * Edit is to a KumaScript template
        * User has the SPAM_EXEMPTED_FLAG
        """
        client_ready = super(RevisionForm, self).akismet_enabled()
        user_exempted = waffle.flag_is_active(self.request, SPAM_EXEMPTED_FLAG)
        return client_ready and not user_exempted and not self.is_template

    @property
    def akismet_error_message(self):
        request = getattr(self, 'request', None)
        user = request and request.user
        return mark_safe(render_to_string('wiki/includes/spam_error.html',
                                          {'user': user}))

    def akismet_error(self, parameters, exception=None):
        """
        Upon errors from the Akismet API records the user, document
        and date of the attempt for further analysis. Then call the
        parent class' error handler.
        """
        try:
            document = self.instance.document
        except ObjectDoesNotExist:
            document = None

        if exception and isinstance(exception, AkismetError):
            # For Akismet errors, save the submission and exception details
            dsa_params = parameters.copy()
            dsa_params['akismet_status_code'] = exception.status_code
            dsa_params['akismet_debug_help'] = exception.debug_help
            dsa_params['akismet_response'] = exception.response.content
            review = DocumentSpamAttempt.AKISMET_ERROR
        else:
            # For detected spam, save the details for review
            dsa_params = parameters
            review = DocumentSpamAttempt.NEEDS_REVIEW

        # Wrapping this in a try/finally to make sure that even if
        # creating a spam attempt object fails we call the parent
        # method that raises a ValidationError
        try:
            DocumentSpamAttempt.objects.create(
                title=self.cleaned_data['title'],
                slug=self.cleaned_data['slug'],
                user=self.request.user,
                document=document,
                data=json.dumps(dsa_params, indent=2, sort_keys=True),
                review=review
            )
        finally:
            if not waffle.flag_is_active(self.request, SPAM_TRAINING_FLAG):
                super(RevisionForm, self).akismet_error(parameters, exception)

    def akismet_parameters(self):
        """
        Returns the parameters for Akismet's check-comment API endpoint.

        The form cleaning also saves the data into the instance, which will
        cause future calls to return different data. The results during the
        initial form cleaning are cached in ._akismet_data, and returned for
        future calls, such as the unit tests.
        """
        if not getattr(self, '_akismet_data', None):
            try:
                document = self.instance.document
            except ObjectDoesNotExist:
                self._akismet_data = AkismetNewDocumentData(
                    self.request, self.cleaned_data, self.data.get('locale'))
            else:
                if document.current_revision:
                    self._akismet_data = AkismetEditDocumentData(
                        self.request, self.cleaned_data, document)
                else:
                    # New translation, compare to English document
                    based_on = self.cleaned_data.get('based_on')
                    assert based_on, 'Expected a new translation.'
                    document = based_on.document
                    self._akismet_data = AkismetNewTranslationData(
                        self.request, self.cleaned_data, document,
                        self.data.get('locale'))

        parameters = self._akismet_data.parameters.copy()
        parameters.update(self.akismet_parameter_overrides())
        return parameters

    def save(self, document, **kwargs):
        """
        Persists the revision and returns it.
        Takes the view request and document of the revision.
        Does some specific things when the revision is fully saved.
        """
        # have to check for first edit before we save
        is_first_edit = not self.request.user.wiki_revisions().exists()

        # Making sure we don't commit the saving right away since we
        # want to do other things here.
        kwargs['commit'] = False

        if self.section_id and self.instance and self.instance.document:
            # The logic to save a section is slightly different and may
            # need to evolve over time; a section edit doesn't submit
            # all the fields, and we need to account for that when we
            # construct the new Revision.
            doc = Document.objects.get(pk=self.instance.document.id)
            old_rev = doc.current_revision
            new_rev = super(RevisionForm, self).save(**kwargs)
            new_rev.document = document
            new_rev.creator = self.request.user
            new_rev.toc_depth = old_rev.toc_depth
            new_rev.save()
            new_rev.review_tags.set(*list(old_rev.review_tags.names()))

        else:
            new_rev = super(RevisionForm, self).save(**kwargs)
            new_rev.document = document
            new_rev.creator = self.request.user
            new_rev.toc_depth = self.cleaned_data['toc_depth']
            new_rev.save()
            new_rev.review_tags.set(*self.cleaned_data['review_tags'])
            new_rev.localization_tags.set(*self.cleaned_data['localization_tags'])

            # when enabled store the user's IP address
            if waffle.switch_is_active('store_revision_ips'):
                RevisionIP.objects.log(
                    revision=new_rev,
                    headers=self.request.META,
                    data=json.dumps(self.akismet_parameters(),
                                    indent=2, sort_keys=True)
                )

            # send first edit emails
            if is_first_edit:
                send_first_edit_email.delay(new_rev.pk)

            # schedule a document rendering
            document.schedule_rendering('max-age=0')

            # schedule event notifications
            EditDocumentEvent(new_rev).fire(exclude=new_rev.creator)

        return new_rev


class RevisionAkismetSubmissionAdminForm(AkismetSubmissionFormMixin,
                                         forms.ModelForm):
    """
    A model form used in the admin UI to submit missed spam or ham.

    In the Django admin, an admin can both mark a revision as missed spam,
    and correct an incorrectly marked spam.

    The ``AkismetSubmissionFormMixin`` class submits the data to Akismet in
    the ``clean`` method, using the override methods in this and derived
    classes.  Users of the form must set the ``sender`` to the request user
    before calling ``is_valid()``.
    """
    class Meta(object):
        model = RevisionAkismetSubmission
        exclude = ['sender', 'sent']

    def akismet_submission_type(self):
        """The submission type is determined from the submitted form data."""
        return self.cleaned_data['type']

    def akismet_parameters(self):
        """
        Returns parameter dict to pass to Akismet's submission API endpoints.
        """
        revision = self.cleaned_data['revision']
        akismet_data = AkismetHistoricalData(revision, self.request)
        return akismet_data.parameters


class RevisionAkismetSubmissionSpamForm(RevisionAkismetSubmissionAdminForm):
    """
    A model form for submitting missed spam.

    For public dashboards, the only valid submission type is spam, so the
    type is omitted from the form and hard-coded as "spam".
    """

    class Meta(RevisionAkismetSubmissionAdminForm.Meta):
        exclude = ['sender', 'sent', 'type']

    def akismet_submission_type(self):
        """Force the submission type to spam."""
        return "spam"


class TreeMoveForm(forms.Form):
    title = StrippedCharField(min_length=1, max_length=255,
                              required=False,
                              widget=forms.TextInput(
                                  attrs={'placeholder': TITLE_PLACEHOLDER}),
                              label=_(u'Title:'),
                              help_text=_(u'Title of article'),
                              error_messages={'required': TITLE_REQUIRED,
                                              'min_length': TITLE_SHORT,
                                              'max_length': TITLE_LONG})
    slug = StrippedCharField(min_length=1, max_length=255,
                             widget=forms.TextInput(),
                             label=_(u'New slug:'),
                             help_text=_(u'New article URL'),
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
