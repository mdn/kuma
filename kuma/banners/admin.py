from django.contrib import admin

from .models import Banner


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    actions = ['activate_all', 'deactivate_all']
    list_display = ('banner_name', 'banner_active', 'banner_priority')
    fields = ('banner_name', 'banner_title', 'banner_copy',
              'banner_button_copy', 'banner_theme', 'banner_active',
              'banner_priority')
    search_fields = ('banner_name', 'banner_active')
    ordering = ('banner_priority',)

    def activate_all(self, request, queryset):
        rows_updated = queryset.update(banner_active=True)
        if rows_updated == 1:
            message_bit = '1 banner was'
        else:
            message_bit = '%s banners were ' % rows_updated
        self.message_user(request, '%s successfully marked as active.' % message_bit)

    def deactivate_all(self, request, queryset):
        rows_updated = queryset.update(banner_active=False)
        if rows_updated == 1:
            message_bit = '1 banner was'
        else:
            message_bit = '%s banners were ' % rows_updated
        self.message_user(request, '%s successfully deactived.' % message_bit)

    activate_all.short_description = 'Activate all selected banners'
    deactivate_all.short_description = 'Deactivate all selected banners'
