from django.contrib import admin

from users.models import UserBan


class UserBanAdmin(admin.ModelAdmin):
    fields = ('user', 'by', 'reason', 'is_active')
    list_display = ('user', 'by', 'reason')
    list_filter = ('is_active',)
    raw_id_fields = ('user',)
    search_fields = ('user', 'reason')


admin.site.register(UserBan, UserBanAdmin)
