from django import template
from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.util import get_deleted_objects
from django.contrib.admin.util import model_ngettext
from django.core.exceptions import PermissionDenied
from django.shortcuts import render_to_response
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy, ugettext as _

from taggit_extras.managers import NamespacedTaggableManager
from taggit.forms import TagWidget, TagField

from .models import Submission



def censor_selected(self, request, queryset):
    """
    Censor the selected submissions, with confirmation interstitial.

    Largely stolen from django.contrib.admin.actions.delete_selected
    """
    opts = self.model._meta
    app_label = opts.app_label

    # Check that the user has delete permission for the actual model
    if not self.has_delete_permission(request):
        raise PermissionDenied

    # The user has already confirmed the deletion.
    # Do the deletion and return a None to display the change list view again.
    if request.POST.get('post'):
        censored_url = request.POST.get('censored_url', None)
        n = queryset.count()
        if n:
            for obj in queryset:
                obj.censor(url=censored_url)
                obj_display = force_unicode(obj)
                self.message_user(request, _("Censored %(item)s") % {
                    "item": obj_display
                })
            self.message_user(request,
                _("Successfully censored %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(self.opts, n)
                })
        # Return None to display the change list page again.
        return None

    context = {
        "title": _("Are you sure?"),
        "object_name": force_unicode(opts.verbose_name),
        'queryset': queryset,
        "opts": opts,
        "root_path": self.admin_site.root_path,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

    # Display the confirmation page
    tmpl_name = 'admin/demos/submission/censor_selected_confirmation.html'
    return render_to_response(tmpl_name, context,
            context_instance=template.RequestContext(request))

censor_selected.short_description = "Censor selected submissions"


def delete_selected(modeladmin, request, queryset):
    """
    The out-of-box Django delete never calls Submission.delete(), so this is a
    mostly redundant lift-and-hack to ensure that happens. This is important
    because Submission.delete() also cleans up its uploaded files.

    See also: https://docs.djangoproject.com/en/dev/ref/contrib/admin/actions/
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Check that the user has delete permission for the actual model
    if not modeladmin.has_delete_permission(request):
        raise PermissionDenied

    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    deletable_objects, perms_needed = get_deleted_objects(queryset, opts,
            request.user, modeladmin.admin_site, levels_to_root=2)

    # The user has already confirmed the deletion.
    # Do the deletion and return a None to display the change list view again.
    if request.POST.get('post'):
        if perms_needed:
            raise PermissionDenied
        n = queryset.count()
        if n:
            for obj in queryset:
                obj_display = force_unicode(obj)
                modeladmin.log_deletion(request, obj, obj_display)
                obj.delete()
                modeladmin.message_user(request,
                    _("Deleted and uploaded files for %(item)s") % {
                        "item": obj_display
                    })
            modeladmin.message_user(request,
                _("Successfully deleted %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })
        # Return None to display the change list page again.
        return None

    context = {
        "title": _("Are you sure?"),
        "object_name": force_unicode(opts.verbose_name),
        "deletable_objects": [deletable_objects],
        'queryset': queryset,
        "perms_lacking": perms_needed,
        "opts": opts,
        "root_path": modeladmin.admin_site.root_path,
        "app_label": app_label,
        'action_checkbox_name': helpers.ACTION_CHECKBOX_NAME,
    }

    # Display the confirmation page
    return render_to_response(
        modeladmin.delete_selected_confirmation_template or [
            "admin/%s/%s/delete_selected_confirmation.html" %
                (app_label, opts.object_name.lower()),
            "admin/%s/delete_selected_confirmation.html" % app_label,
            "admin/delete_selected_confirmation.html"
        ], context, context_instance=template.RequestContext(request))

delete_selected.short_description = ugettext_lazy(
    "Delete selected %(verbose_name_plural)s")


class SubmissionAdmin(admin.ModelAdmin):
    actions = (delete_selected, censor_selected,)

    list_display = ('title', 'creator', 'featured', 'censored', 'hidden',
                    'taggit_tags', 'modified', )

    list_editable = ('featured', 'taggit_tags', )

    search_fields = ('title', 'summary', 'description', 'taggit_tags__name')

    list_filter = ('censored', 'hidden', 'created', 'modified')

    readonly_fields = ('censored',)

    formfield_overrides = {
        NamespacedTaggableManager: {
            "widget": TagWidget(attrs={"size": 70})
        }
    }

    def queryset(self, request):
        return Submission.admin_manager

admin.site.register(Submission, SubmissionAdmin)
