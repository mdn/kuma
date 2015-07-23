from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from taggit.forms import TagWidget

from kuma.core.managers import NamespacedTaggableManager
from .models import User, UserBan


class UserBanAdmin(admin.ModelAdmin):
    fields = ('user', 'by', 'reason', 'is_active')
    list_display = ('user', 'by', 'reason', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    raw_id_fields = ('user', 'by')
    search_fields = ('user__username', 'reason', 'by__username')

admin.site.register(UserBan, UserBanAdmin)


class UserAdmin(BaseUserAdmin):
    """
    Extends the admin view of users to show date_joined field
    add a filter on the field too
    """
    list_display = ('username', 'fullname', 'email', 'title', 'organization',
                    'location', 'content_flagging_email', 'tags',
                    'date_joined', 'is_staff', 'is_active')
    list_editable = ('content_flagging_email', 'tags')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    ordering = ('-date_joined',)
    search_fields = ('username', 'homepage', 'title', 'fullname',
                     'organization', 'location', 'bio', 'misc',
                     'email', 'tags__name')

    formfield_overrides = {
        NamespacedTaggableManager: {
            'widget': TagWidget(attrs={'size': 45})
        }
    }

admin.site.register(User, UserAdmin)
