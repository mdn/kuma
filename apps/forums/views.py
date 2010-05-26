from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.views.decorators.http import require_POST

import jingo
from authority.decorators import permission_required_or_403

from sumo.urlresolvers import reverse
from sumo.utils import paginate
from .models import Forum, Thread
from .forms import ReplyForm, NewThreadForm
import forums as constants


def forums(request):
    """
    View all the forums.
    """

    forums_ = paginate(request, Forum.objects.all())

    return jingo.render(request, 'forums.html', {'forums': forums_})


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
    """
    View all the threads in a forum.
    """

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

    return jingo.render(request, 'threads.html',
                        {'forum': forum, 'threads': threads_,
                         'sort': sort, 'desc_toggle': desc_toggle,
                         'feed_url': feed_url})


def posts(request, forum_slug, thread_id):
    """
    View all the posts in a thread.
    """

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id)

    posts_ = paginate(request, thread.post_set.all(),
                      constants.POSTS_PER_PAGE)

    form = ReplyForm({'thread': thread.id, 'author': request.user.id})

    feed_url = reverse('forums.posts.feed',
                       kwargs={'forum_slug': forum_slug,
                       'thread_id': thread_id})

    return jingo.render(request, 'posts.html',
                        {'forum': forum, 'thread': thread,
                         'posts': posts_, 'form': form,
                         'feed_url': feed_url})


def reply(request, forum_slug, thread_id):
    """
    Reply to a thread.
    """
    form = ReplyForm(request.POST)

    if form.is_valid():
        thread = Thread.objects.get(pk=thread_id)
        reply = form.save(commit=False)
        reply.thread = thread
        reply.author = request.user
        reply.save()

        return HttpResponseRedirect(reply.get_absolute_url())

    return jingo.render(request, 'bad_reply.html')


@login_required
def new_thread(request, forum_slug):
    """Start a new thread."""

    forum = get_object_or_404(Forum, slug=forum_slug)

    if request.method == 'GET':
        form = NewThreadForm()
        return jingo.render(request, 'new_thread.html',
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
            reverse('forums.posts',
                    kwargs={'forum_slug': thread.forum.slug,
                            'thread_id': thread.id}))

    return jingo.render(request, 'bad_reply.html')

@require_POST
@login_required
@permission_required_or_403('forums_forum.thread_locked_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def lock_thread(request, forum_slug, thread_id):
    """Lock/Unlock a thread."""

    forum = get_object_or_404(Forum, slug=forum_slug)
    thread = get_object_or_404(Thread, pk=thread_id)

    thread.is_locked = not thread.is_locked
    thread.save()

    return HttpResponseRedirect(
            reverse('forums.posts',
                    kwargs={'forum_slug': thread.forum.slug,
                            'thread_id': thread.id}))


@login_required
@permission_required_or_403('forums_forum.thread_sticky_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def sticky_thread(request, forum_slug, thread_id):
    """Mark/unmark a thread sticky."""

    return jingo.render(request, 'bad_reply.html')


@login_required
@permission_required_or_403('forums_forum.thread_edit_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def edit_thread(request, forum_slug, thread_id):
    """Edit a thread."""

    return jingo.render(request, 'bad_reply.html')


@login_required
@permission_required_or_403('forums_forum.thread_delete_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def delete_thread(request, forum_slug, thread_id):
    """Delete a thread."""

    return jingo.render(request, 'bad_reply.html')


@login_required
@permission_required_or_403('forums_forum.post_edit_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def edit_post(request, forum_slug, thread_id, post_id):
    """Edit a post."""

    return jingo.render(request, 'bad_reply.html')


@login_required
@permission_required_or_403('forums_forum.post_delete_forum',
                            (Forum, 'slug__iexact', 'forum_slug'))
def delete_post(request, forum_slug, thread_id, post_id):
    """Delete a post."""

    return jingo.render(request, 'bad_reply.html')
