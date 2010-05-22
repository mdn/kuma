from .models import Forum

import authority


class ForumPermission(authority.permissions.BasePermission):
    label = 'forums_forum'
    checks = ('thread_edit', 'thread_sticky', 'thread_locked',
              'thread_delete', 'post_edit', 'post_delete')

authority.register(Forum, ForumPermission)
