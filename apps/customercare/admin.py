from django.contrib import admin

from .models import Tweet, CannedCategory, CannedResponse, CategoryMembership


class TweetAdmin(admin.ModelAdmin):
    date_hierarchy = 'created'
    list_display = ('tweet_id', '__unicode__', 'created', 'locale')
    list_filter = ('locale',)
    search_fields = ('raw_json',)
admin.site.register(Tweet, TweetAdmin)


class MembershipInline(admin.StackedInline):
    """Inline to show response/category relationships."""
    extra = 1
    model = CategoryMembership
    raw_id_fields = ('response',)


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('title', 'locale', 'weight', 'response_count')
    inlines = (MembershipInline,)

    def response_count(self, obj):
        return obj.responses.count()
admin.site.register(CannedCategory, CategoryAdmin)


class ResponseAdmin(admin.ModelAdmin):
    list_display = ('title', 'locale', 'category_count')
    inlines = (MembershipInline,)

    def category_count(self, obj):
        return obj.categories.count()
admin.site.register(CannedResponse, ResponseAdmin)
