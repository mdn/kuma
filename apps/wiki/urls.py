from django.conf.urls.defaults import patterns, url, include

from kbforums.feeds import ThreadsFeed, PostsFeed
from sumo.views import redirect_to


# These patterns inherit from /discuss
discuss_patterns = patterns('kbforums.views',
    url(r'^$', 'threads', name='wiki.discuss.threads'),
    url(r'^/feed', ThreadsFeed(), name='wiki.discuss.threads.feed'),
    url(r'^/new', 'new_thread', name='wiki.discuss.new_thread'),
    url(r'^/watch', 'watch_forum', name='wiki.discuss.watch_forum'),
    url(r'^/(?P<thread_id>\d+)$', 'posts', name='wiki.discuss.posts'),
    url(r'^/(?P<thread_id>\d+)/feed$', PostsFeed(),
        name='wiki.discuss.posts.feed'),
    url(r'^/(?P<thread_id>\d+)/watch$', 'watch_thread',
        name='wiki.discuss.watch_thread'),
    url(r'^/(?P<thread_id>\d+)/reply$', 'reply', name='wiki.discuss.reply'),
    url(r'^/(?P<thread_id>\d+)/sticky$', 'sticky_thread',
        name='wiki.discuss.sticky_thread'),
    url(r'^/(?P<thread_id>\d+)/lock$', 'lock_thread',
        name='wiki.discuss.lock_thread'),
    url(r'^/(?P<thread_id>\d+)/edit$', 'edit_thread',
        name='wiki.discuss.edit_thread'),
    url(r'^/(?P<thread_id>\d+)/delete$', 'delete_thread',
        name='wiki.discuss.delete_thread'),
    url(r'^/(?P<thread_id>\d+)/(?P<post_id>\d+)/edit', 'edit_post',
        name='wiki.discuss.edit_post'),
    url(r'^/(?P<thread_id>\d+)/(?P<post_id>\d+)/delete', 'delete_post',
        name='wiki.discuss.delete_post'),
)

# These patterns inherit (?P<document_slug>[^\/]).
document_patterns = patterns('wiki.views',
    url(r'^$', 'document', name='wiki.document'),
    url(r'^/revision/(?P<revision_id>\d+)$', 'revision',
        name='wiki.revision'),
    url(r'^/history$', 'document_revisions', name='wiki.document_revisions'),
    url(r'^/edit$', 'edit_document', name='wiki.edit_document'),
    url(r'^/edit/(?P<revision_id>\d+)$', 'edit_document',
        name='wiki.new_revision_based_on'),
    url(r'^/review/(?P<revision_id>\d+)$', 'review_revision',
        name='wiki.review_revision'),
    url(r'^/compare$', 'compare_revisions', name='wiki.compare_revisions'),
    url(r'^/translate$', 'translate', name='wiki.translate'),
    url(r'^/locales$', 'select_locale', name='wiki.select_locale'),

    # Un/Subscribe to document edit notifications.
    url(r'^/watch$', 'watch_document', name='wiki.document_watch'),
    url(r'^/unwatch$', 'unwatch_document', name='wiki.document_unwatch'),

    # Vote helpful/not helpful
    url(r'^/vote', 'helpful_vote', name="wiki.document_vote"),

    # KB discussion forums
    (r'^/discuss', include(discuss_patterns)),

    # Delete a revision
    url(r'^/revision/(?P<revision_id>\d+)/delete$', 'delete_revision',
        name='wiki.delete_revision'),
)

urlpatterns = patterns('wiki.views',
    url(r'^/$', redirect_to, {'url': 'home'}, name='wiki.home'),

    # Un/Subscribe to locale 'ready for review' notifications.
    url(r'^/watch-ready-for-review$', 'watch_locale',
        name='wiki.locale_watch'),
    url(r'^/unwatch-ready-for-review$', 'unwatch_locale',
        name='wiki.locale_unwatch'),
    url(r'^/json$', 'json_view', name='wiki.json'),

    url(r'^/new$', 'new_document', name='wiki.new_document'),
    url(r'^/all$', 'list_documents', name='wiki.all_documents'),
    url(r'^/preview-wiki-content$', 'preview_revision', name='wiki.preview'),
    url(r'^/category/(?P<category>\d+)$', 'list_documents',
        name='wiki.category'),
    url(r'^/tag/(?P<tag>[^/]+)$', 'list_documents', name='wiki.tag'),
    (r'^/(?P<document_slug>[^/]+)', include(document_patterns)),
)
