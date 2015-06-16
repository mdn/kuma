from datetime import datetime

from django.contrib import admin
from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.http import HttpResponse, HttpResponseRedirect
from django.template.response import TemplateResponse

from kuma.core.decorators import login_required, permission_required
from kuma.core.urlresolvers import reverse

from .decorators import check_readonly
from .models import (Document, DocumentZone, DocumentTag,
                     Revision, RevisionIP, EditorToolbar)


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


def undelete_documents(self, request, queryset):
    for doc in queryset:
        doc.undelete()
undelete_documents.short_description = "Undelete deleted documents"


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
        except:
            bad_count += 1
            pass
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


def related_revisions_link(self):
    """HTML link to related revisions for admin change list"""
    link = '%s?%s' % (
        reverse('admin:wiki_revision_changelist', args=[]),
        'document__exact=%s' % (self.id)
    )
    count = self.revisions.count()
    what = (count == 1) and 'revision' or 'revisions'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

related_revisions_link.allow_tags = True
related_revisions_link.short_description = "All Revisions"


def current_revision_link(self):
    """HTML link to the current revision for the admin change list"""
    if not self.current_revision:
        return "None"
    rev = self.current_revision
    rev_url = reverse('admin:wiki_revision_change', args=[rev.id])
    return '<a href="%s">Current&nbsp;Revision&nbsp;(#%s)</a>' % (rev_url, rev.id)

current_revision_link.allow_tags = True
current_revision_link.short_description = "Current Revision"


def parent_document_link(self):
    """HTML link to the topical parent document for admin change list"""
    if not self.parent:
        return ''
    url = reverse('admin:wiki_document_change', args=[self.parent.id])
    return '<a href="%s">Translated&nbsp;from&nbsp;(#%s)</a>' % (url, self.parent.id)

parent_document_link.allow_tags = True
parent_document_link.short_description = "Translation Parent"


def topic_parent_document_link(self):
    """HTML link to the parent document for admin change list"""
    if not self.parent_topic:
        return ''
    url = reverse('admin:wiki_document_change',
                  args=[self.parent_topic.id])
    return '<a href="%s">Topic&nbsp;Parent&nbsp;(#%s)</a>' % (url, self.parent_topic.id)

topic_parent_document_link.allow_tags = True
topic_parent_document_link.short_description = "Parent Document"


def topic_children_documents_link(self):
    """HTML link to a list of child documents"""
    count = self.children.count()
    if not count:
        return ''
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (self.id)
    )
    what = (count == 1) and 'child' or 'children'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

topic_children_documents_link.allow_tags = True
topic_children_documents_link.short_description = "Child Documents"


def topic_sibling_documents_link(self):
    """HTML link to a list of sibling documents"""
    if not self.parent_topic:
        return ''
    count = self.parent_topic.children.count()
    if not count:
        return ''
    link = '%s?%s' % (
        reverse('admin:wiki_document_changelist', args=[]),
        'parent_topic__exact=%s' % (self.parent_topic.id)
    )
    what = (count == 1) and 'sibling' or 'siblings'
    return '<a href="%s">%s&nbsp;%s</a>' % (link, count, what)

topic_sibling_documents_link.allow_tags = True
topic_sibling_documents_link.short_description = "Sibling Documents"


def document_link(self):
    """Public link to the document"""
    link = self.get_absolute_url()
    return ('<a target="_blank" href="%s">'
            '<img src="/media/img/icons/link_external.png"> View</a>' %
            (link,))

document_link.allow_tags = True
document_link.short_description = "Public"


def combine_funcs(self, funcs):
    """Combine several field functions into one block of lines"""
    out = (x(self) for x in funcs)
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % x for x in out if x)


def document_nav_links(self):
    """Combine the document hierarchy nav links"""
    return combine_funcs(self, (
        parent_document_link,
        topic_parent_document_link,
        topic_sibling_documents_link,
        topic_children_documents_link,
    ))

document_nav_links.allow_tags = True
document_nav_links.short_description = "Hierarchy"


def revision_links(self):
    """Combine the revision nav links"""
    return combine_funcs(self, (
        current_revision_link,
        related_revisions_link,
    ))

revision_links.allow_tags = True
revision_links.short_description = "Revisions"


def rendering_info(self):
    """Combine the rendering times into one block"""
    return '<ul>%s</ul>' % ''.join('<li>%s</li>' % (x % y) for x, y in (
        ('<img src="/admin-media/img/admin/icon-yes.gif" alt="%s"> '
         'Deferred rendering', self.defer_rendering),
        ('%s (last)', self.last_rendered_at),
        ('%s (started)', self.render_started_at),
        ('%s (scheduled)', self.render_scheduled_at),
    ) if y)

rendering_info.allow_tags = True
rendering_info.short_description = 'Rendering'
rendering_info.admin_order_field = 'last_rendered_at'


class DocumentAdmin(admin.ModelAdmin):

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
               undelete_documents)
    change_list_template = 'admin/wiki/document/change_list.html'
    fields = ('locale', 'title', 'defer_rendering', 'render_expires',
              'render_max_age', 'parent', 'parent_topic', 'category',)
    list_display = ('id', 'locale', 'slug', 'title',
                    document_link,
                    'modified',
                    'render_expires', 'render_max_age',
                    rendering_info,
                    document_nav_links,
                    revision_links,)
    list_display_links = ('id', 'slug',)
    list_filter = ('defer_rendering', 'is_template', 'is_localizable',
                   'category', 'locale', 'deleted')
    raw_id_fields = ('parent', 'parent_topic',)
    readonly_fields = ('id', 'current_revision')
    search_fields = ('title', 'slug', 'html', 'current_revision__tags')

    def get_actions(self, request):
        """
        Remove the built-in delete action, since it bypasses the model
        delete() method (bad) and we want people using the non-admin
        deletion UI anyway.

        """
        actions = super(DocumentAdmin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        """
        Disable deletion of individual Documents, by always returning
        False for the permission check.

        """
        return False

    def get_queryset(self, request):
        """
        The Document class has multiple managers which perform
        different filtering based on deleted status; we want the
        special admin-only one that doesn't filter.
        """
        qs = Document.admin_objects.all()
        # TODO: When we're on a Django version that handles admin
        # queryset ordering in a better way, we can stop doing this
        # part.
        ordering = self.get_ordering(request)
        if ordering:
            qs = qs.order_by(*ordering)
        return qs


class RevisionAdmin(admin.ModelAdmin):
    fields = ('title', 'summary', 'content', 'keywords', 'tags',
              'comment', 'is_approved')
    list_display = ('id', 'slug', 'title', 'is_approved', 'created',
                    'creator',)
    list_display_links = ('id', 'slug')
    list_filter = ('is_approved', )
    ordering = ('-created',)
    search_fields = ('title', 'slug', 'summary', 'content', 'tags')


class RevisionIPAdmin(admin.ModelAdmin):
    readonly_fields = ('revision', 'ip',)
    list_display = ('revision', 'ip',)


class DocumentTagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug')
    search_fields = ('name',)
    ordering = ('name',)


class DocumentZoneAdmin(admin.ModelAdmin):
    raw_id_fields = ('document',)


admin.site.register(Document, DocumentAdmin)
admin.site.register(DocumentZone, DocumentZoneAdmin)
admin.site.register(DocumentTag, DocumentTagAdmin)
admin.site.register(Revision, RevisionAdmin)
admin.site.register(RevisionIP, RevisionIPAdmin)
admin.site.register(EditorToolbar, admin.ModelAdmin)
