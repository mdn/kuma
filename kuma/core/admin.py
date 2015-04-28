from django.contrib import admin

from kuma.core.models import IPBan


class IPBanAdmin(admin.ModelAdmin):
    # Remove list delete action to enforce model soft delete in admin site
    actions = None
    readonly_fields = ('deleted',)
    list_display = ('ip', 'created', 'deleted')


admin.site.register(IPBan, IPBanAdmin)
