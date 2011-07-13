from django.contrib import admin

from .models import UserProfile, Calendar, Event


class ProfileAdmin(admin.ModelAdmin):
    list_display = ('user_name',)
    search_fields = ['user__username']

    def user_name(self, obj):
        return obj.user.username
    user_name.short_description = 'username'

admin.site.register(UserProfile, ProfileAdmin)
admin.site.register(Calendar, admin.ModelAdmin)
admin.site.register(Event, admin.ModelAdmin)
