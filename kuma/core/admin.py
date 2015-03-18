from django.contrib import admin

from kuma.core.models import IPBan


class IPBanAdmin(admin.ModelAdmin):
    list_display = ('ip', 'created', 'deleted')


admin.site.register(IPBan, IPBanAdmin)
