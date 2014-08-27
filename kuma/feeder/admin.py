from django.contrib import admin

from .models import Feed, Entry, Bundle


class BundleInline(admin.TabularInline):
    model = Bundle.feeds.through


class FeedAdmin(admin.ModelAdmin):
    inlines = [BundleInline]
admin.site.register(Feed, FeedAdmin)


class EntryAdmin(admin.ModelAdmin):
    pass
admin.site.register(Entry, EntryAdmin)


class BundleAdmin(admin.ModelAdmin):
    pass
admin.site.register(Bundle, BundleAdmin)
