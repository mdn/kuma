import logging

from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect, Http404
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

import jingo
from authority.decorators import permission_required_or_403

from access.decorators import has_perm_or_owns_or_403
from sumo.urlresolvers import reverse
from sumo.utils import paginate
from .models import Forum, Thread, Post
from .forms import ReplyForm, NewThreadForm, EditThreadForm, EditPostForm
from notifications import create_watch, check_watch, destroy_watch
import forums as constants

log = logging.getLogger('k.forums')


def forums(request):
    """View all the forums."""

    forums_ = paginate(request, Forum.objects.all())

    return jingo.render(request, 'forums/forums.html', {'forums': forums_})


def sort_threads(threads_, sort=0, desc=0):
    if desc:
        prefix = '-'
    else:
        prefix = ''

    if sort == 3:
        return threads_.order_by(prefix + 'creator__username').all()
    elif sort == 4:
        return threads_.order_by(prefix + 'replies').all()
    elif sort == 5:
        return threads_.order_by(prefix + 'last_post__created').all()

    # If nothing matches, use default sorting
    return threads_.all()


def threads(request, forum_slug):
    """View all the threads in a forum."""

    forum = get_object_or_404(Forum, slug=forum_slug)

    try:
        sort = int(request.GET.get('sort', 0))
    except ValueError:
        sort = 0

    try:
        desc = int(request.GET.get('desc', 0))
    except ValueError:
        desc = 0
    desc_toggle = 0 if desc else 1

    threads_ = sort_threads(forum.thread_set, sort, desc)
    threads_ = paginate(request, threads_,
                        per_page=constants.THREADS_PER_PAGE)

    feed_url = reverse('forums.threads.feed',
                       kwargs={'forum_slug': forum_slug})

    return jingo.render(request, 'forums/threads.html',
                        {'forum': forum, 'threads': threads_,
                         'sort': sort, 'desc_toggle': desc_toggle,
                         'feed_url': feed_url})


def posts(request, forum_slug, thread_id, form=None):
    """View all the posts in a thread."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)

    posts_ = paginate(request, thread.post_set.all(),
                      constants.POSTS_PER_PAGE)

    if not form:
        form = ReplyForm()

    feed_url = reverse('forums.posts.feed',
                       kwargs={'forum_slug': forum_slug,
                       'thread_id': thread_id})

    return jingo.render(request, 'forums/posts.html',
                        {'forum': forum, 'thread': thread,
                         'posts': posts_, 'form': form,
                         'feed_url': feed_url})


@login_required
def reply(request, forum_slug, thread_id):
    """Reply to a thread."""
    form = ReplyForm(request.POST)

    if form.is_valid():
        forum = get_object_or_404(Forum, slug=forum_slug)
        thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
        if not thread.is_locked:
            reply_ = form.save(commit=False)
            reply_.thread = thread
            reply_.author = request.user
            reply_.save()

            return HttpResponseRedirect(reply_.get_absolute_url())

    return posts(request, forum_slug, thread_id, form)


@login_required
def new_thread(request, forum_slug):
    """Start a new thread."""

    forum = get_object_or_404(Forum, slug=forum_slug)

    if request.method == 'GET':
        form = NewThreadForm()
        return jingo.render(request, 'forums/new_thread.html',
                            {'form': form, 'forum': forum})

    form = NewThreadForm(request.POST)

    if form.is_valid():
        thread = forum.thread_set.create(creator=request.user,
                                         title=form.cleaned_data['title'])
        thread.save()
        post = thread.new_post(author=request.user,
                               content=form.cleaned_data['content'])
        post.save()

        return HttpResponseRedirect(
            reverse('forums.posts', args=[forum_slug, thread.id]))

    return jingo.render(request, 'forums/new_thread.html',
                        {'form': form, 'forum': forum})


@require_POST
@login_required
@permission_required_or_403('forums_forum.thread_locked_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def lock_thread(request, forum_slug, thread_id):
    """Lock/Unlock a thread."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    thread.is_locked = not thread.is_locked
    log.info("User %s set is_locked=%s on thread with id=%s " %
             (request.user, thread.is_locked, thread.id))
    thread.save()

    return HttpResponseRedirect(
        reverse('forums.posts', args=[forum_slug, thread_id]))


@require_POST
@login_required
@permission_required_or_403('forums_forum.thread_sticky_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def sticky_thread(request, forum_slug, thread_id):
    """Mark/unmark a thread sticky."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    thread.is_sticky = not thread.is_sticky
    log.info("User %s set is_sticky=%s on thread with id=%s " %
             (request.user, thread.is_sticky, thread.id))
    thread.save()

    return HttpResponseRedirect(
        reverse('forums.posts', args=[forum_slug, thread_id]))


@login_required
@has_perm_or_owns_or_403('forums_forum.thread_edit_forum', 'creator',
                         (Thread, 'id__iexact', 'thread_id'),
                         (Forum, 'slug__iexact', 'forum_slug'))
def edit_thread(request, forum_slug, thread_id):
    """Edit a thread."""
    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)

    if thread.is_locked:
        raise PermissionDenied

    if request.method == 'GET':
        form = EditThreadForm(instance=thread)
        return jingo.render(request, 'forums/edit_thread.html',
                            {'form': form, 'forum': forum, 'thread': thread})

    form = EditThreadForm(request.POST)

    if form.is_valid():
        log.warning('User %s is editing thread with id=%s' %
                    (request.user, thread.id))
        thread.title = form.cleaned_data['title']
        thread.save()

        url = reverse('forums.posts', args=[forum_slug, thread_id])
        return HttpResponseRedirect(url)

    return jingo.render(request, 'forums/edit_thread.html',
                        {'form': form, 'forum': forum, 'thread': thread})


@login_required
@permission_required_or_403('forums_forum.thread_delete_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def delete_thread(request, forum_slug, thread_id):
    """Delete a thread."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'forums/confirm_thread_delete.html',
                            {'forum': forum, 'thread': thread})

    # Handle confirm delete form POST
    log.warning('User %s is deleting thread with id=%s' %
                (request.user, thread.id))
    thread.delete()

    return HttpResponseRedirect(reverse('forums.threads', args=[forum_slug]))


@login_required
@has_perm_or_owns_or_403('forums_forum.post_edit_forum', 'author',
                         (Post, 'id__iexact', 'post_id'),
                         (Forum, 'slug__iexact', 'forum_slug'))
def edit_post(request, forum_slug, thread_id, post_id):
    """Edit a post."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    post = get_object_or_404(Post, pk=post_id, thread=thread)

    if thread.is_locked:
        raise PermissionDenied

    if request.method == 'GET':
        form = EditPostForm({'content': post.content})
        return jingo.render(request, 'forums/edit_post.html',
                            {'form': form, 'forum': forum,
                             'thread': thread, 'post': post})

    form = EditPostForm(request.POST)

    if form.is_valid():
        log.warning('User %s is editing post with id=%s' %
                    (request.user, post.id))
        post.content = form.cleaned_data['content']
        post.updated_by = request.user
        post.save()

        return HttpResponseRedirect(post.get_absolute_url())

    return jingo.render(request, 'forums/edit_post.html',
                        {'form': form, 'forum': forum,
                         'thread': thread, 'post': post})


@login_required
@permission_required_or_403('forums_forum.post_delete_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def delete_post(request, forum_slug, thread_id, post_id):
    """Delete a post."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)
    post = get_object_or_404(Post, pk=post_id, thread=thread)

    if request.method == 'GET':
        # Render the confirmation page
        return jingo.render(request, 'forums/confirm_post_delete.html',
                            {'forum': forum, 'thread': thread,
                             'post': post})

    # Handle confirm delete form POST
    log.warning("User %s is deleting post with id=%s" %
                (request.user, post.id))
    post.delete()
    try:
        Thread.objects.get(pk=thread_id)
        goto = reverse('forums.posts', args=[forum_slug, thread_id])
    except Thread.DoesNotExist:
        # The thread was deleted, go to the threads list page
        goto = reverse('forums.threads', args=[forum_slug])

    return HttpResponseRedirect(goto)


@login_required
@require_POST
def watch_thread(request, forum_slug, thread_id):
    """Start watching a thread."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id, forum=forum)

    try:
        if check_watch(Thread, thread.id, request.user.email):
            destroy_watch(Thread, thread.id, request.user.email)
        else:
            create_watch(Thread, thread.id, request.user.email)
    except Thread.DoesNotExist:
        raise Http404

    return HttpResponseRedirect(reverse('forums.posts',
                                        args=[forum_slug, thread_id]))
