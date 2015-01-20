from django.contrib import admin

from .models import ActionCounterUnique


class ActionCounterUniqueAdmin(admin.ModelAdmin):
    list_display = ('content_object', 'name', 'total', 'user', 'ip',
                    'user_agent', 'modified')

admin.site.register(ActionCounterUnique, ActionCounterUniqueAdmin)
