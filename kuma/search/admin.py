from django.contrib import admin, messages
from django.utils.translation import ugettext_lazy as _

from .forms import IndexModelForm
from .models import Filter, FilterGroup, Index


def promote(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request,
                       _("Can't promote more than one index at once."))
        return
    index = queryset[0]
    index.promote()
    messages.info(request, _("Promoted search index %s.") % index)
promote.short_description = _("Promote selected search index to current index")


def demote(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request, _("Can't demote more than one index at once."))
        return
    if Index.objects.filter(promoted=True, populated=True).count() <= 1:
        messages.error(request, _("Can't demote the index if there is only "
                                  "one. Create and populate a new one first."))
        return
    index = queryset[0]
    index.demote()
    messages.info(request, _("Demoted search index %s.") % index)
demote.short_description = _("Demote selected search index "
                             "(automatic fallback to previous index)")


def populate(modeladmin, request, queryset):
    if queryset.count() > 1:
        messages.error(request,
                       _("Can't populate more than one index at once."))
        return
    index = queryset[0]
    message = index.populate()
    messages.info(request, message)
populate.short_description = _("Populate selected search index via Celery")


class IndexAdmin(admin.ModelAdmin):
    list_display = ('name', 'promoted', 'populated', 'current',
                    'created_at')
    ordering = ('-created_at',)
    actions = [populate, promote, demote]
    readonly_fields = ['promoted', 'populated']
    list_filter = ('promoted', 'populated', 'created_at')
    form = IndexModelForm

    def current(self, obj):
        return obj.prefixed_name == Index.objects.get_current().prefixed_name
    current.short_description = _('Is current index?')
    current.boolean = True


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
admin.site.register(Index, IndexAdmin)
