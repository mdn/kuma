# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib import admin

from .models import ContentFlag


class ContentFlagAdmin(admin.ModelAdmin):
    list_display = ( 'created', 'content_view_link', 'content_admin_link',
            'flag_status', 'flag_type', 'explanation', )
    list_editable = ( 'flag_status', )
    list_filter = ( 'flag_status', 'flag_type', )
    list_select_related = True

admin.site.register(ContentFlag, ContentFlagAdmin)
