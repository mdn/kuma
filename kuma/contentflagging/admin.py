from django.contrib import admin

from .models import ContentFlag


class ContentFlagAdmin(admin.ModelAdmin):
    list_display = ('created', 'content_view_link', 'content_admin_link',
                    'flag_status', 'flag_type', 'explanation')
    list_editable = ('flag_status',)
    list_filter = ('flag_status', 'flag_type', 'content_type')
    list_select_related = True

admin.site.register(ContentFlag, ContentFlagAdmin)
