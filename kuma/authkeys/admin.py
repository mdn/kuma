from django.contrib import admin
from django.utils.html import format_html

from kuma.core.urlresolvers import reverse

from .models import Key, KeyAction


def history_link(self):
    url = (
        f'{reverse("admin:authkeys_keyaction_changelist")}'
        f'?key__exact={self.id}')
    count = self.history.count()
    what = 'action' if count == 1 else 'actions'
    return format_html('<a href="{}">{}&nbsp;{}</a>', url, count, what)


history_link.short_description = 'Usage history'


@admin.register(Key)
class KeyAdmin(admin.ModelAdmin):
    fields = ('description',)
    list_display = ('id', 'user', 'created', history_link, 'key',
                    'description')
    ordering = ('-created', 'user')
    search_fields = ('key', 'description', 'user__username')


def key_link(self):
    key = self.key
    url = reverse('admin:authkeys_key_change',
                  args=[key.id])
    return format_html('<a href="{}">{} (#{})</a>', url, key.user, key.id)


key_link.short_description = 'Key'


def content_object_link(self):
    obj = self.content_object
    url_key = f'admin:{obj._meta.app_label}_{obj._meta.model_name}_change'
    url = reverse(url_key, args=[obj.id])
    return format_html('<a href="{}">{} (#{})</a>', url, self.content_type, obj.pk)


content_object_link.short_description = 'Object'


@admin.register(KeyAction)
class KeyActionAdmin(admin.ModelAdmin):
    fields = ('notes',)
    list_display = ('id', 'created', key_link, 'action',
                    content_object_link, 'notes')
    list_filter = ('action', 'content_type')
    ordering = ('-id',)
    search_fields = ('action', 'key__key', 'key__user__username', 'notes')
