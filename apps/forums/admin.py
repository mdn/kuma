from django.contrib import admin
from forums.models import Forum


class ForumAdmin(admin.ModelAdmin):
    exclude = ('last_post',)
    prepopulated_fields = {'slug': ('name',)}

admin.site.register(Forum, ForumAdmin)
