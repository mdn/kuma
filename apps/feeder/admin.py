# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

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
