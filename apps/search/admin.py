from django.contrib import admin

from .models import Filter, FilterGroup


class FilterGroupAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)
    ordering = ('-order', 'name')


class FilterAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'group', 'enabled')
    list_filter = ('group',)
    search_fields = ('name', 'slug')
    list_editable = ('enabled',)
    list_select_related = True
    radio_fields = {
        'operator': admin.VERTICAL,
        'group': admin.VERTICAL,
    }


admin.site.register(FilterGroup, FilterGroupAdmin)
admin.site.register(Filter, FilterAdmin)
