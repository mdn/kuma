# -*- coding: utf-8 -*-

from datetime import datetime
import json

from django.contrib import admin
from django.contrib import messages
from django.conf import settings
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse
from django.template.defaultfilters import linebreaksbr, truncatechars
from django.utils import timezone
from django.utils.encoding import smart_text
from django.utils.html import escape
from django.utils.safestring import mark_safe
from django.utils.text import Truncator
from waffle import flag_is_active

from kuma.core.admin import DisabledDeletionMixin
from kuma.core.decorators import login_required, permission_required
from kuma.core.urlresolvers import reverse
from kuma.spam import constants
from kuma.spam.akismet import Akismet, AkismetError

from .decorators import check_readonly
from .forms import RevisionAkismetSubmissionAdminForm
from .models import (Document, DocumentDeletionLog, DocumentSpamAttempt,
                     DocumentTag, DocumentZone, EditorToolbar, Revision,
                     RevisionAkismetSubmission, RevisionIP)


def dump_selected_documents(self, request, queryset):
    filename = "documents_%s.json" % (datetime.now().isoformat(),)
    response = HttpResponse(content_type="text/plain")
    response['Content-Disposition'] = 'attachment; filename=%s' % filename
    Document.objects.dump_json(queryset, response)
    return response

dump_selected_documents.short_description = "Dump selected documents as JSON"


def repair_breadcrumbs(self, request, queryset):
    for doc in queryset:
        doc.repair_breadcrumbs()
repair_breadcrumbs.short_description = "Repair translation breadcrumbs"


def purge_documents(self, request, queryset):
    redirect_url = '/admin/wiki/document/purge/?ids=%s'
    selected = request.POST.getlist(admin.ACTION_CHECKBOX_NAME)
    return HttpResponseRedirect(redirect_url % ','.join(selected))
purge_documents.short_description = "Permanently purge deleted documents"


@login_required
@staff_member_required
@permission_required('wiki.purge_document')
@check_readonly
def purge_view(request):
    """
    Interstitial admin view for purging multiple Documents.
    """
    selected = request.GET.get('ids', '').split(',')
    to_purge = Document.deleted_objects.filter(id__in=selected)
    if request.method == 'POST':
        if request.POST.get('confirm_purge', False):
            purged = 0
            for doc in to_purge:
                doc.purge()
                purged += 1
            messages.info(request, "%s document(s) were purged." % purged)
        return HttpResponseRedirect('/admin/wiki/document/')
    return TemplateResponse(request,
                            'admin/wiki/purge_documents.html',
                            {'to_purge': to_purge})


def restore_documents(self, request, queryset):
    for doc in queryset:
        doc.restore()
restore_documents.short_description = "Restore deleted documents"


def enable_deferred_rendering_for_documents(self, request, queryset):
    queryset.update(defer_rendering=True)
    self.message_user(request, 'Enabled deferred rendering for %s Documents' %
                               queryset.count())
enable_deferred_rendering_for_documents.short_description = (
    "Enable deferred rendering for selected documents")


def disable_deferred_rendering_for_documents(self, request, queryset):
    queryset.update(defer_rendering=False)
    self.message_user(request, 'Disabled deferred rendering for %s Documents' %
                               queryset.count())
disable_deferred_rendering_for_documents.short_description = (
    "Disable deferred rendering for selected documents")


def force_render_documents(self, request, queryset):
    count, bad_count = 0, 0
    for doc in queryset:
        try:
            doc.render(cache_control='no-cache')
            count += 1
        except Exception:
            bad_count += 1
    self.message_user(request, "Rendered %s documents, failed on %s "
                               "documents." % (count, bad_count))
force_render_documents.short_description = (
    "Perform rendering for selected documents")


def resave_current_revision(self, request, queryset):
    count, bad_count = 0, 0
    for doc in queryset:
        if not doc.current_revision:
            bad_count += 1
        else:
            doc.current_revision.save()
            count += 1
    self.message_user(request, "Resaved current revision for %s documents. %s "
                               "documents had no current revision." %
                               (count, bad_count))

resave_current_revision.short_description = (
    "Re-save current revision for selected documents")


def related_revisions_link(obj):
    """HTML link to related revisions for admin change list"""
    link = '%s?%s' % (
        reverse('admin:wiki_revision_changelist', args=[]),
        'document__exact=%s' % (obj.id)
    )
    count = obj.revisions.count()
    what = (count == 1) and 'revision' or 'revisions'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

related_revisions_link.allow_tags = True
related_revisions_link.short_description = "All Revisions"


def current_revision_link(obj):
    """HTML link to the current revision for the admin change list"""
    if not obj.current_revision:
        return "None"
    rev = obj.current_revision
    rev_url = reverse('admin:wiki_revision_change', args=[rev.id])
    return '<a href="%s">Current&nbsp;Revision&nbsp;(#%s)</a>' % (rev_url, rev.id)

current_revision_link.allow_tags = True
current_revision_link.short_description = "Current Revision"


def parent_document_link(obj):
    """HTML link to the topical parent document for admin change list"""
    if not obj.parent:
        return ''
    url = reverse('admin:wiki_document_change', args=[obj.parent.id])
    return '<a href="%s">Translated&nbsp;from&nbsp;(#%s)</a>' % (url, obj.parent.id)

parent_document_link.allow_tags = True
parent_document_link.short_description = "Translation Parent"


def topic_parent_document_link(obj):
    """HTML link to the parent document for admin change list"""
    if not obj.parent_topic:
        return ''
    url = reverse('admin:wiki_document_change',
                  args=[obj.parent_topic.id])
    return '<a href="%s">Topic&nbsp;Parent&nbsp;(#%s)</a>' % (url, obj.parent_topic.id)

topic_parent_document_link.allow_tags = True
topic_parent_document_link.short_description = "Parent Document"


def topic_children_documents_link(obj):
    """HTML link to a list of child documents"""
    count = obj.children.count()
    if not count:
        return ''
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (obj.id)
    )
    what = (count == 1) and 'child' or 'children'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

topic_children_documents_link.allow_tags = True
topic_children_documents_link.short_description = "Child Documents"


def topic_sibling_documents_link(obj):
    """HTML link to a list of sibling documents"""
    if not obj.parent_topic:
        return ''
    count = obj.parent_topic.children.count()
    if not count:
        return ''
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (obj.parent_topic.id)
    )
    what = (count == 1) and 'sibling' or 'siblings'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

topic_sibling_documents_link.allow_tags = True
topic_sibling_documents_link.short_description = "Sibling Documents"


def document_link(obj):
    """Public link to the document"""
    link = obj.get_absolute_url()
    return ('<a target="_blank" href="%s">'
            '<img src="%simg/icons/link_external.png"> View</a>' %
            (link, settings.STATIC_URL))

document_link.allow_tags = True
document_link.short_description = "Public"


def combine_funcs(obj, funcs):
    """Combine several field functions into one block of lines"""
    out = (x(obj) for x in funcs)
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % x for x in out if x)


def document_nav_links(obj):
    """Combine the document hierarchy nav links"""
    return combine_funcs(obj, (
        parent_document_link,
        topic_parent_document_link,
        topic_sibling_documents_link,
        topic_children_documents_link,
    ))

document_nav_links.allow_tags = True
document_nav_links.short_description = "Hierarchy"


def revision_links(obj):
    """Combine the revision nav links"""
    return combine_funcs(obj, (
        current_revision_link,
        related_revisions_link,
    ))

revision_links.allow_tags = True
revision_links.short_description = "Revisions"


def rendering_info(obj):
    """Combine the rendering times into one block"""
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % (x % y) for x, y in (
        ('<img src="%s/admin/img/admin/icon-yes.gif" alt="%s"> '
         'Deferred rendering', (settings.STATIC_URL, obj.defer_rendering)),
        ('%s (last)', obj.last_rendered_at),
        ('%s (started)', obj.render_started_at),
        ('%s (scheduled)', obj.render_scheduled_at),
    ) if y)

rendering_info.allow_tags = True
rendering_info.short_description = 'Rendering'
rendering_info.admin_order_field = 'last_rendered_at'


@admin.register(Document)
class DocumentAdmin(DisabledDeletionMixin, admin.ModelAdmin):

    class Media:
        js = ('js/wiki-admin.js',)

    list_per_page = 25
    actions = (dump_selected_documents,
               resave_current_revision,
               force_render_documents,
               enable_deferred_rendering_for_documents,
               disable_deferred_rendering_for_documents,
               repair_breadcrumbs,
               purge_documents,
               restore_documents)
    change_list_template = 'admin/wiki/document/change_list.html'
    fieldsets = (
        (None, {
            'fields': ('locale', 'title')
        }),
        ('Rendering', {
            'fields': ('defer_rendering', 'render_expires', 'render_max_age')
        }),
        ('Topical Hierarchy', {
            'fields': ('parent_topic',)
        }),
        ('Localization', {
            'description': "The document should be <strong>either</strong> "
                           "localizable, <strong>or</strong> have a parent - "
                           "never both.",
            'fields': ('is_localizable', 'parent')
        })
    )
    list_display = ('id', 'locale', 'slug', 'title',
                    document_link,
                    'modified',
                    'render_expires', 'render_max_age',
                    rendering_info,
                    document_nav_links,
                    revision_links,)
    list_display_links = ('id', 'slug',)
    list_filter = ('defer_rendering', 'is_template', 'is_localizable',
                   'locale', 'deleted')
    raw_id_fields = ('parent', 'parent_topic',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title', 'slug', 'html', 'current_revision__tags')

    def get_queryset(self, request):
        """
        The Document class has multiple managers which perform
        different filtering based on deleted status; we want the
        special admin-only one that doesn't filter.
        """
        return Document.admin_objects.all()


@admin.register(DocumentDeletionLog)
class DocumentDeletionLogAdmin(DisabledDeletionMixin, admin.ModelAdmin):
    list_display = ['slug', 'locale', 'user', 'timestamp']
    list_filter = ['timestamp', 'locale']
    search_fields = ['slug', 'reason']
    ordering = ['-timestamp']
    readonly_fields = ['locale', 'slug', 'user', 'timestamp']


@admin.register(DocumentTag)
class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    ordering = ('name',)


@admin.register(DocumentZone)
class DocumentZoneAdmin(admin.ModelAdmin):
    raw_id_fields = ('document',)

SUBMISSION_NOT_AVAILABLE = 'Akismet submission not available.'


@admin.register(DocumentSpamAttempt)
class DocumentSpamAttemptAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'user', 'title_short', 'slug_short', 'doc_short', 'review']
    list_display_links = ['id', 'title_short', 'slug_short']
    list_filter = [
        'created', 'review', 'document__deleted', 'document__locale']
    list_editable = ('review',)
    ordering = ['-created']
    search_fields = ['title', 'slug', 'user__username']
    raw_id_fields = ['user', 'document']
    fields = [
        'created', 'user', 'title', 'slug', 'document', 'submitted_data',
        'review', 'reviewed', 'reviewer']
    readonly_fields = ['created', 'submitted_data', 'reviewer', 'reviewed']

    MAX_LENGTH = 25

    def title_short(self, obj):
        return truncatechars(obj.title, self.MAX_LENGTH)
    title_short.short_description = 'Title'

    def slug_short(self, obj):
        return truncatechars(obj.slug, self.MAX_LENGTH)
    slug_short.short_description = 'Slug'

    def doc_short(self, obj):
        u"""
        Shorten document 'path (name)' representation in list view.

        The important part is having an HTML break character such as a space,
        so truncating paths as well as long titles, to look like:

        /en-US/docs/Start/Of/Slug… (The start of the title…)
        """
        doc = obj.document
        if doc:
            full_path = u'/%s/docs/%s' % (doc.locale, doc.slug)
            if len(full_path) <= self.MAX_LENGTH:
                path = full_path
            else:
                path = Truncator(full_path).chars(self.MAX_LENGTH, u'…')
            title = Truncator(doc.title).chars(self.MAX_LENGTH, u'…')
            return u'%s (%s)' % (path, title)
        else:
            return mark_safe('<em>new document</em>')
    doc_short.short_description = 'Document (if edit)'

    class NotEnabled(Exception):
        """Akismet is not enabled"""

    def submit_ham(self, request, data):
        """Submit new ham to Akismet.

        This is done directly with the Akismet client rather than the form
        classes, so that bulk edits can be made in the admin list view.

        It will raise NotEnabled or AkismetError if something goes wrong.
        """
        client = Akismet()
        if not client.ready:
            raise self.NotEnabled('Akismet is not configured.')
        spam_submission = flag_is_active(request,
                                         constants.SPAM_SUBMISSIONS_FLAG)
        if not spam_submission:
            raise self.NotEnabled('Akismet spam submission is not enabled.')
        user_ip = data.pop('user_ip', '')
        user_agent = data.pop('user_agent', '')
        client.submit_ham(user_ip=user_ip, user_agent=user_agent, **data)

    def save_model(self, request, obj, form, change):
        """If reviewed, set the reviewer, and submit ham as requested."""
        send_ham = (obj.review == DocumentSpamAttempt.HAM and
                    obj.reviewed is None and obj.data is not None)
        if obj.review in (DocumentSpamAttempt.HAM, DocumentSpamAttempt.SPAM):
            obj.reviewer = obj.reviewer or request.user
            obj.reviewed = obj.reviewed or timezone.now()
        if send_ham:
            data = json.loads(obj.data)
            try:
                self.submit_ham(request, data)
            except (self.NotEnabled, AkismetError) as error:
                obj.reviewer = None
                obj.reviewed = None
                obj.review = DocumentSpamAttempt.NEEDS_REVIEW
                message = (
                    'Unable to submit ham for document spam attempt %s: %s' %
                    (obj, error))
                self.message_user(request, message, level=messages.ERROR)
            else:
                message = 'Submitted ham for document spam attempt %s' % obj
                self.message_user(request, message, level=messages.INFO)
        obj.save()

    def submitted_data(self, instance):
        return instance.data or SUBMISSION_NOT_AVAILABLE


@admin.register(Revision)
class RevisionAdmin(admin.ModelAdmin):
    fields = ('title', 'summary', 'content', 'keywords', 'tags',
              'comment', 'is_approved')
    list_display = ('id', 'slug', 'title', 'is_approved', 'created',
                    'creator')
    list_display_links = ('id', 'slug')
    list_filter = ('is_approved',)
    ordering = ('-created',)
    search_fields = ('title', 'slug', 'summary', 'content', 'tags')


@admin.register(RevisionIP)
class RevisionIPAdmin(admin.ModelAdmin):
    readonly_fields = ('revision', 'ip', 'user_agent', 'referrer',
                       'submitted_data')
    list_display = ('revision', 'ip')

    def submitted_data(self, obj):
        """Display Akismet data, if saved at edit time."""
        return obj.data or SUBMISSION_NOT_AVAILABLE


@admin.register(RevisionAkismetSubmission)
class RevisionAkismetSubmissionAdmin(DisabledDeletionMixin, admin.ModelAdmin):
    form = RevisionAkismetSubmissionAdminForm
    radio_fields = {'type': admin.VERTICAL}
    raw_id_fields = ['revision']
    list_display = ['id', 'sent', 'revision_with_link', 'type', 'sender']
    list_display_links = ['id', 'sent']
    list_filter = ['type', 'sent']
    search_fields = ('sender__username', 'revision__id', 'revision__title')

    def get_fields(self, request, obj=None):
        if obj is None:
            return ['type', 'revision']
        else:
            return super(RevisionAkismetSubmissionAdmin,
                         self).get_fields(request, obj)

    def revision_with_link(self, obj):
        """Link to the revision public page"""
        if obj.revision_id:
            admin_link = obj.revision.get_absolute_url()
            return ('<a target="_blank" href="%s">%s</a>' %
                    (admin_link, escape(obj.revision)))
        else:
            return 'None'
    revision_with_link.allow_tags = True
    revision_with_link.short_description = "Revision"

    def get_readonly_fields(self, request, obj=None):
        """
        Hook for specifying custom readonly fields.
        """
        if obj:
            return ['type', 'revision', 'sender', 'sent']
        else:
            return ['sender', 'sent']

    def save_model(self, request, obj, form, change):
        obj.sender = request.user
        obj.save()

    def get_form(self, request, obj=None, **kwargs):
        AdminForm = super(RevisionAkismetSubmissionAdmin,
                          self).get_form(request, obj=obj, **kwargs)

        class AdminFormWithRequest(AdminForm):
            """
            A ad-hoc admin form that has access to the current request.

            Sigh.
            """
            def __new__(cls, *args, **kwargs):
                return AdminForm(request, *args, **kwargs)

        return AdminFormWithRequest

    def add_view(self, request, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['submitted_data'] = self.submitted_data(request)
        return super(RevisionAkismetSubmissionAdmin, self).add_view(
            request, form_url, extra_context=extra_context)

    def change_view(self, request, object_id, form_url='', extra_context=None):
        extra_context = extra_context or {}
        extra_context['submitted_data'] = self.submitted_data(
            request, object_id)
        return super(RevisionAkismetSubmissionAdmin, self).change_view(
            request, object_id, form_url, extra_context=extra_context)

    def submitted_data(self, request, obj_id=None):
        """Display Akismet data, if saved at edit time."""
        if obj_id:
            obj = RevisionAkismetSubmission.objects.get(id=obj_id)
        else:
            obj = None

        if obj and obj.revision_id:
            revision_ip = obj.revision.revisionip_set.first()
        else:
            revision_id = request.GET.get('revision')
            if revision_id:
                revision_ip = RevisionIP.objects.filter(
                    revision_id=revision_id).first()
            else:
                revision_ip = None
        if revision_ip and revision_ip.data:
            return linebreaksbr(smart_text(revision_ip.data))
        else:
            return SUBMISSION_NOT_AVAILABLE


@admin.register(EditorToolbar)
class EditorToolbarAdmin(admin.ModelAdmin):
    list_display = ['name', 'creator', 'default']
    list_filters = ['default']
    raw_id_fields = ['creator']
