from .models import Forum

import authority


class ForumPermission(authority.permissions.BasePermission):
    label = 'forums_forum'
    checks = ('thread_edit', 'thread_sticky', 'thread_locked', 'thread_delete',
              'post_edit', 'post_delete', 'thread_move', 'view_in', 'post_in')
    # view_in: view the forum, its threads, and its posts
    # post_in: make new threads and posts in a forum

authority.register(Forum, ForumPermission)
