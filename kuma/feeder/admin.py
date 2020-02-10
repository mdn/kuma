from django.contrib import admin

from .models import Bundle, Entry, Feed


class BundleInline(admin.TabularInline):
    model = Bundle.feeds.through


@admin.register(Feed)
class FeedAdmin(admin.ModelAdmin):
    inlines = [BundleInline]


@admin.register(Entry)
class EntryAdmin(admin.ModelAdmin):
    pass


@admin.register(Bundle)
class BundleAdmin(admin.ModelAdmin):
    pass
