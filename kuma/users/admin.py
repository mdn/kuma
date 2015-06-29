from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from kuma.core.urlresolvers import reverse

from taggit.forms import TagWidget

from kuma.core.managers import NamespacedTaggableManager
from .models import User, UserBan, UserProfile


class UserAdmin(BaseUserAdmin):
    # extend the admin view of users to show date_joined field; add a filter on the field too
    list_display = ('username', 'email', 'first_name', 'last_name',
                    'date_joined', 'is_staff', 'is_active')
    list_filter = ('is_staff', 'is_superuser', 'is_active', 'date_joined')
    ordering = ('-date_joined',)

admin.site.register(User, UserAdmin)


class UserBanAdmin(admin.ModelAdmin):
    fields = ('user', 'by', 'reason', 'is_active')
    list_display = ('user', 'by', 'reason', 'is_active')
    list_editable = ('is_active',)
    list_filter = ('is_active',)
    raw_id_fields = ('user', 'by')
    search_fields = ('user__username', 'reason', 'by__username')

admin.site.register(UserBan, UserBanAdmin)


class ProfileAdmin(admin.ModelAdmin):

    list_display = ('user_name', 'related_user', 'fullname', 'title',
                    'organization', 'location', 'content_flagging_email',
                    'tags')

    list_editable = ('content_flagging_email', 'tags', )

    search_fields = ('user__username', 'homepage', 'title', 'fullname',
                     'organization', 'location', 'bio', 'misc',
                     'user__email', 'tags__name')

    list_filter = ()

    formfield_overrides = {
        NamespacedTaggableManager: {
            "widget": TagWidget(attrs={"size": 45})
        }
    }

    def related_user(self, obj):
        """HTML link to related user account"""
        link = reverse('admin:users_user_change', args=(obj.user.id,),
                       current_app=admin.site.name)
        # TODO: Needs l10n? Maybe not a priority for an admin page.
        return ('<a href="%(link)s"><strong>User %(id)s</strong></a>' %
                {'link': link, 'id': obj.user.id})
    related_user.allow_tags = True
    related_user.short_description = 'User account'

    def user_name(self, obj):
        return obj.user.username
    user_name.short_description = 'User name'


admin.site.register(UserProfile, ProfileAdmin)
