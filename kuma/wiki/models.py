from datetime import datetime
from uuid import uuid4

from django.conf import settings
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import gettext_lazy as _
from taggit.managers import TaggableManager
from taggit.models import ItemBase, TagBase

from .content import Extractor
from .managers import (
    AllDocumentManager,
    DeletedDocumentManager,
    DocumentAdminManager,
    DocumentManager,
    RevisionIPManager,
    TaggedDocumentManager,
)


class DocumentTag(TagBase):
    """A tag indexing a document"""

    class Meta:
        verbose_name = _("Document Tag")
        verbose_name_plural = _("Document Tags")


class TaggedDocument(ItemBase):
    """Through model, for tags on Documents"""

    content_object = models.ForeignKey("Document", on_delete=models.CASCADE)
    tag = models.ForeignKey(
        DocumentTag,
        related_name="%(app_label)s_%(class)s_items",
        on_delete=models.CASCADE,
    )

    objects = TaggedDocumentManager()


class DocumentAttachment(models.Model):
    """
    Intermediary between Documents and Attachments. Allows storing the
    user who attached a file to a document, and a (unique for that
    document) name for referring to the file from the document.
    """

    file = models.ForeignKey(
        "attachments.Attachment",
        related_name="document_attachments",
        on_delete=models.PROTECT,
    )
    document = models.ForeignKey(
        "wiki.Document", related_name="attached_files", on_delete=models.CASCADE
    )
    attached_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL
    )
    name = models.TextField()

    # whether or not this attachment was uploaded for the document
    is_original = models.BooleanField(
        verbose_name=_("uploaded to the document"),
        default=False,
    )

    # whether or not this attachment is linked in the document's content
    is_linked = models.BooleanField(
        verbose_name=_("linked in the document content"),
        default=False,
    )

    class Meta:
        db_table = "attachments_documentattachment"

    def __str__(self):
        return '"%s" for document "%s"' % (self.file, self.document)


class Document(models.Model):
    """A localized knowledgebase document, not revision-specific."""

    title = models.CharField(max_length=255, db_index=True)
    slug = models.CharField(max_length=255, db_index=True)

    # NOTE: Documents are indexed by tags, but tags are edited in Revisions.
    # Also, using a custom through table to isolate Document tags from those
    # used in other models and apps. (Works better than namespaces, for
    # completion and such.)
    tags = TaggableManager(through=TaggedDocument)

    # DEPRECATED: Is this document a template or not?
    # Droping or altering this column will require a table rebuild, so it
    # should be done in a maintenance window.
    is_template = models.BooleanField(default=False, editable=False, db_index=True)

    # Is this a redirect or not?
    is_redirect = models.BooleanField(default=False, editable=False, db_index=True)

    # Is this document localizable or not?
    is_localizable = models.BooleanField(default=True, db_index=True)

    locale = models.CharField(
        max_length=7,
        choices=settings.SORTED_LANGUAGES,
        default=settings.WIKI_DEFAULT_LANGUAGE,
        db_index=True,
    )

    # Latest approved revision. L10n dashboard depends on this being so (rather
    # than being able to set it to earlier approved revisions).
    current_revision = models.ForeignKey(
        "Revision", null=True, related_name="current_for+", on_delete=models.SET_NULL
    )

    # The Document I was translated from. NULL if this doc is in the default
    # locale or it is nonlocalizable. TODO: validate against
    # settings.WIKI_DEFAULT_LANGUAGE.
    parent = models.ForeignKey(
        "self",
        related_name="translations",
        null=True,
        blank=True,
        on_delete=models.PROTECT,
    )

    parent_topic = models.ForeignKey(
        "self", related_name="children", null=True, blank=True, on_delete=models.PROTECT
    )

    # The files attached to the document, represented by a custom intermediate
    # model so we can store some metadata about the relation
    files = models.ManyToManyField(
        "attachments.Attachment",
        through=DocumentAttachment,
    )

    # JSON representation of Document for API results, built on save
    json = models.TextField(editable=False, blank=True, null=True)

    # Raw HTML of approved revision's wiki markup
    html = models.TextField(editable=False)

    # Cached result of kumascript and other offline processors (if any)
    rendered_html = models.TextField(editable=False, blank=True, null=True)

    # Errors (if any) from the last rendering run
    rendered_errors = models.TextField(editable=False, blank=True, null=True)

    # Whether or not to automatically defer rendering of this page to a queued
    # offline task. Generally used for complex pages that need time
    defer_rendering = models.BooleanField(default=False, db_index=True)

    # Timestamp when this document was last scheduled for a render
    render_scheduled_at = models.DateTimeField(null=True, db_index=True)

    # Timestamp when a render for this document was last started
    render_started_at = models.DateTimeField(null=True, db_index=True)

    # Timestamp when this document was last rendered
    last_rendered_at = models.DateTimeField(null=True, db_index=True)

    # Maximum age (in seconds) before this document needs re-rendering
    render_max_age = models.IntegerField(blank=True, null=True)

    # Time after which this document needs re-rendering
    render_expires = models.DateTimeField(blank=True, null=True, db_index=True)

    # Whether this page is deleted.
    deleted = models.BooleanField(default=False, db_index=True)

    # Last modified time for the document. Should be equal-to or greater than
    # the current revision's created field
    modified = models.DateTimeField(auto_now=True, null=True, db_index=True)

    body_html = models.TextField(editable=False, blank=True, null=True)

    quick_links_html = models.TextField(editable=False, blank=True, null=True)

    toc_html = models.TextField(editable=False, blank=True, null=True)

    summary_html = models.TextField(editable=False, blank=True, null=True)

    summary_text = models.TextField(editable=False, blank=True, null=True)

    uuid = models.UUIDField(default=uuid4, editable=False)

    class Meta(object):
        unique_together = (
            ("parent", "locale"),
            ("slug", "locale"),
        )
        permissions = (
            ("move_tree", "Can move a tree of documents"),
            ("purge_document", "Can permanently delete document"),
            ("restore_document", "Can restore deleted document"),
        )

    objects = DocumentManager()
    deleted_objects = DeletedDocumentManager()
    all_objects = AllDocumentManager()
    admin_objects = DocumentAdminManager()

    def __str__(self):
        return "%s (%s)" % (self.slug, self.title)

    @cached_property
    def extract(self):
        return Extractor(self)


class DocumentDeletionLog(models.Model):
    """
    Log of who deleted a Document, when, and why.
    """

    # We store the locale/slug because it's unique, and also because a
    # ForeignKey would delete this log when the Document gets purged.
    locale = models.CharField(
        max_length=7,
        choices=settings.SORTED_LANGUAGES,
        default=settings.WIKI_DEFAULT_LANGUAGE,
        db_index=True,
    )

    slug = models.CharField(max_length=255, db_index=True)

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    timestamp = models.DateTimeField(auto_now=True)
    reason = models.TextField()

    def __str__(self):
        return "/%(locale)s/%(slug)s deleted by %(user)s" % {
            "locale": self.locale,
            "slug": self.slug,
            "user": self.user,
        }


class ReviewTag(TagBase):
    """A tag indicating review status, mainly for revisions"""

    class Meta:
        verbose_name = _("Review Tag")
        verbose_name_plural = _("Review Tags")


class LocalizationTag(TagBase):
    """A tag indicating localization status, mainly for revisions"""

    class Meta:
        verbose_name = _("Localization Tag")
        verbose_name_plural = _("Localization Tags")


class ReviewTaggedRevision(ItemBase):
    """Through model, just for review tags on revisions"""

    content_object = models.ForeignKey("Revision", on_delete=models.CASCADE)
    tag = models.ForeignKey(
        ReviewTag,
        related_name="%(app_label)s_%(class)s_items",
        on_delete=models.CASCADE,
    )


class LocalizationTaggedRevision(ItemBase):
    """Through model, just for localization tags on revisions"""

    content_object = models.ForeignKey("Revision", on_delete=models.CASCADE)
    tag = models.ForeignKey(
        LocalizationTag,
        related_name="%(app_label)s_%(class)s_items",
        on_delete=models.CASCADE,
    )


class Revision(models.Model):
    """A revision of a localized knowledgebase document"""

    # Depth of table-of-contents in document display.
    TOC_DEPTH_NONE = 0
    TOC_DEPTH_ALL = 1
    TOC_DEPTH_H2 = 2
    TOC_DEPTH_H3 = 3
    TOC_DEPTH_H4 = 4

    TOC_DEPTH_CHOICES = (
        (TOC_DEPTH_NONE, _("No table of contents")),
        (TOC_DEPTH_ALL, _("All levels")),
        (TOC_DEPTH_H2, _("H2 and higher")),
        (TOC_DEPTH_H3, _("H3 and higher")),
        (TOC_DEPTH_H4, _("H4 and higher")),
    )

    document = models.ForeignKey(
        Document, related_name="revisions", on_delete=models.CASCADE
    )

    # Title and slug in document are primary, but they're kept here for
    # revision history.
    title = models.CharField(max_length=255, null=True, db_index=True)
    slug = models.CharField(max_length=255, null=True, db_index=True)

    summary = models.TextField()  # wiki markup
    content = models.TextField()  # wiki markup
    tidied_content = models.TextField(blank=True)  # wiki markup tidied up

    # Keywords are used mostly to affect search rankings. Moderators may not
    # have the language expertise to translate keywords, so we put them in the
    # Revision so the translators can handle them:
    keywords = models.CharField(max_length=255, blank=True)

    # Tags are stored in a Revision as a plain CharField, because Revisions are
    # not indexed by tags. This data is retained for history tracking.
    tags = models.CharField(max_length=255, blank=True)

    # Tags are (ab)used as status flags and for searches, but the through model
    # should constrain things from getting expensive.
    review_tags = TaggableManager(through=ReviewTaggedRevision)

    localization_tags = TaggableManager(through=LocalizationTaggedRevision)

    toc_depth = models.IntegerField(choices=TOC_DEPTH_CHOICES, default=TOC_DEPTH_ALL)

    # Maximum age (in seconds) before this document needs re-rendering
    render_max_age = models.IntegerField(blank=True, null=True)

    created = models.DateTimeField(default=datetime.now, db_index=True)
    comment = models.TextField()
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_revisions",
        on_delete=models.PROTECT,
    )
    is_approved = models.BooleanField(default=True, db_index=True)

    # The default locale's rev that was current when the Edit button was hit to
    # create this revision. Used to determine whether localizations are out of
    # date.
    based_on = models.ForeignKey(
        "self", null=True, blank=True, on_delete=models.SET_NULL
    )
    # TODO: limit_choices_to={'document__locale':
    # settings.WIKI_DEFAULT_LANGUAGE} is a start but not sufficient.

    is_mindtouch_migration = models.BooleanField(
        default=False, db_index=True, help_text="Did this revision come from MindTouch?"
    )

    def save(self, *args, **kwargs):
        if not self.title:
            self.title = self.document.title
        if not self.slug:
            self.slug = self.document.slug

        super(Revision, self).save(*args, **kwargs)

        # When a revision is approved, update document metadata and re-cache
        # the document's html content
        if self.is_approved:
            self.make_current()

    def make_current(self):
        """
        Make this revision the current one for the document
        """
        self.document.title = self.title
        self.document.slug = self.slug
        self.document.html = self.content
        self.document.render_max_age = self.render_max_age
        self.document.current_revision = self
        # Since Revision stores tags as a string, we need to parse them first
        # before setting on the Document.
        self.document.save()

    def __str__(self):
        return "[%s] %s #%s" % (self.document.locale, self.document.title, self.id)


class RevisionIP(models.Model):
    """
    IP Address for a Revision including User-Agent string and Referrer URL.
    """

    revision = models.ForeignKey(Revision, on_delete=models.CASCADE)
    ip = models.CharField(
        _("IP address"),
        max_length=40,
        editable=False,
        db_index=True,
        blank=True,
        null=True,
    )
    user_agent = models.TextField(
        _("User-Agent"),
        editable=False,
        blank=True,
    )
    referrer = models.TextField(
        _("HTTP Referrer"),
        editable=False,
        blank=True,
    )
    data = models.TextField(
        editable=False,
        blank=True,
        null=True,
        verbose_name=_("Data submitted to Akismet"),
    )
    objects = RevisionIPManager()

    def __str__(self):
        return "%s (revision %d)" % (self.ip or "No IP", self.revision.id)


class EditorToolbar(models.Model):
    creator = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        related_name="created_toolbars",
        on_delete=models.CASCADE,
    )
    default = models.BooleanField(default=False)
    name = models.CharField(max_length=100)
    code = models.TextField(max_length=2000)

    def __str__(self):
        return self.name
