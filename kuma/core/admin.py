from django.contrib import admin

from kuma.core.models import IPBan


admin.site.register(IPBan, admin.ModelAdmin)
