from django.contrib import admin
from django.contrib.admin import helpers
from django.contrib.admin.utils import model_ngettext, get_deleted_objects
from django.db import router
from django.core.exceptions import PermissionDenied
from django.template.response import TemplateResponse
from django.utils.encoding import force_unicode
from django.utils.translation import ugettext_lazy, ugettext as _

from kuma.core.managers import NamespacedTaggableManager
from taggit.forms import TagWidget

from .models import Submission


def censor_selected(modeladmin, request, queryset):
    """
    Censor the selected submissions, with confirmation interstitial.

    Largely stolen from django.contrib.admin.actions.delete_selected
    """
    opts = modeladmin.model._meta
    app_label = opts.app_label

    # Check that the user has delete permission for the actual model
    if not modeladmin.has_delete_permission(request):
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
                modeladmin.message_user(request, _("Censored %(item)s") % {
                    "item": obj_display
                })
            modeladmin.message_user(
                request,
                _("Successfully censored %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })
        # Return None to display the change list page again.
        return None

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    context = {
        "title": _("Are you sure?"),
        "object_name": objects_name,
        "queryset": queryset,
        "opts": opts,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
    }

    # Display the confirmation page
    return TemplateResponse(
        request,
        'admin/demos/submission/censor_selected_confirmation.html',
        context, current_app=modeladmin.admin_site.name)
censor_selected.short_description = ugettext_lazy("Censor selected %(verbose_name_plural)s")


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

    using = router.db_for_write(modeladmin.model)

    # Populate deletable_objects, a data structure of all related objects that
    # will also be deleted.
    deletable_objects, perms_needed, protected = get_deleted_objects(
        queryset, opts, request.user, modeladmin.admin_site, using)

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
                modeladmin.message_user(
                    request,
                    _("Deleted and uploaded files for %(item)s") % {
                        "item": obj_display
                    })
            modeladmin.message_user(
                request,
                _("Successfully deleted %(count)d %(items)s.") % {
                    "count": n, "items": model_ngettext(modeladmin.opts, n)
                })
        # Return None to display the change list page again.
        return None

    if len(queryset) == 1:
        objects_name = force_unicode(opts.verbose_name)
    else:
        objects_name = force_unicode(opts.verbose_name_plural)

    if perms_needed or protected:
        title = _("Cannot delete %(name)s") % {"name": objects_name}
    else:
        title = _("Are you sure?")

    context = {
        "title": title,
        "object_name": objects_name,
        "deletable_objects": [deletable_objects],
        "queryset": queryset,
        "perms_lacking": perms_needed,
        "protected": protected,
        "opts": opts,
        "app_label": app_label,
        "action_checkbox_name": helpers.ACTION_CHECKBOX_NAME,
    }

    # Display the confirmation page
    return TemplateResponse(request, modeladmin.delete_selected_confirmation_template or [
        "admin/%s/%s/delete_selected_confirmation.html" % (app_label, opts.object_name.lower()),
        "admin/%s/delete_selected_confirmation.html" % app_label,
        "admin/delete_selected_confirmation.html"
    ], context, current_app=modeladmin.admin_site.name)

delete_selected.short_description = ugettext_lazy("Delete selected %(verbose_name_plural)s")


class SubmissionAdmin(admin.ModelAdmin):
    actions = (delete_selected, censor_selected)

    list_display = ('title', 'creator', 'featured', 'censored', 'hidden',
                    'taggit_tags', 'modified')

    list_editable = ('featured', 'taggit_tags')

    search_fields = ('title', 'summary', 'description', 'taggit_tags__name')

    list_filter = ('censored', 'hidden', 'created', 'modified')

    readonly_fields = ('censored',)

    formfield_overrides = {
        NamespacedTaggableManager: {
            "widget": TagWidget(attrs={"size": 70})
        }
    }

    def get_queryset(self, request):
        return Submission.admin_manager.all()

admin.site.register(Submission, SubmissionAdmin)
