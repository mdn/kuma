from django.contrib import admin
from sumo.urlresolvers import reverse

from taggit_extras.managers import NamespacedTaggableManager
from taggit.forms import TagWidget

from .models import UserBan, UserProfile


class UserBanAdmin(admin.ModelAdmin):
    fields = ('user', 'by', 'reason', 'is_active')
    list_display = ('user', 'by', 'reason')
    list_filter = ('is_active',)
    raw_id_fields = ('user', 'by')
    search_fields = ('user__username', 'reason', 'by__username')


admin.site.register(UserBan, UserBanAdmin)


class ProfileAdmin(admin.ModelAdmin):

    list_display = ('user_name', 'related_user', 'fullname', 'title',
                    'organization', 'location','content_flagging_email',
                    'tags', )

    list_editable = ('content_flagging_email', 'tags', )

    search_fields = ('user__username', 'homepage', 'title', 'fullname',
                     'organization', 'location', 'bio', 'misc',
                     'user__email', 'tags__name', )

    list_filter = ()

    formfield_overrides = {
        NamespacedTaggableManager: {
            "widget": TagWidget(attrs={"size": 45})
        }
    }

    def related_user(self, obj):
        """HTML link to related user account"""
        link = reverse('admin:auth_user_change', args=(obj.user.id,))
        # TODO: Needs l10n? Maybe not a priority for an admin page.
        return ('<a href="%(link)s"><strong>User %(id)s</strong></a>' % dict(
            link=link, id=obj.user.id, username=obj.user.username))

    related_user.allow_tags = True
    related_user.short_description = 'User account'

    def user_name(self, obj):
        return obj.user.username

    user_name.short_description = 'User name'


admin.site.register(UserProfile, ProfileAdmin)
