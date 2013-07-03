# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

from django.contrib import admin

from .models import ActionCounterUnique

class ActionCounterUniqueAdmin(admin.ModelAdmin):
    list_display = ( 'content_object', 'name', 'total', 'user', 'ip',
            'user_agent', 'modified',  )
admin.site.register(ActionCounterUnique, ActionCounterUniqueAdmin)
