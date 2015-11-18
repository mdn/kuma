from django.contrib import admin

from kuma.core.models import IPBan


class DisabledDeletionMixin(object):
    def get_actions(self, request):
        """
        Remove the built-in delete action, since it bypasses the model
        delete() method (bad) and we want people using the non-admin
        deletion UI anyway.
        """
        actions = super(DisabledDeletionMixin, self).get_actions(request)
        if 'delete_selected' in actions:
            del actions['delete_selected']
        return actions

    def has_delete_permission(self, request, obj=None):
        """
        Disable deletion of individual Documents, by always returning
        False for the permission check.
        """
        return False


class IPBanAdmin(admin.ModelAdmin):
    # Remove list delete action to enforce model soft delete in admin site
    actions = None
    readonly_fields = ('deleted',)
    list_display = ('ip', 'created', 'deleted')


admin.site.register(IPBan, IPBanAdmin)
