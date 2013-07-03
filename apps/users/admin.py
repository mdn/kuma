# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib import admin

from users.models import UserBan


class UserBanAdmin(admin.ModelAdmin):
    fields = ('user', 'by', 'reason', 'is_active')
    list_display = ('user', 'by', 'reason')
    list_filter = ('is_active', 'by')
    raw_id_fields = ('user', 'by')
    search_fields = ('user__username', 'reason')


admin.site.register(UserBan, UserBanAdmin)
