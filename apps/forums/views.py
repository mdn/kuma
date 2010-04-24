from django.http import Http404, HttpResponseRedirect
from django.contrib import auth

import jingo

from sumo.urlresolvers import reverse
from .models import Forum, Thread, Post
from .forms import ReplyForm, NewThreadForm


def forums(request):
    """
    View all the forums.
    """

    forums = Forum.objects.all()

    return jingo.render(request, 'forums.html', {'forums': forums})


def threads(request, forum_slug):
    """
    View all the threads in a forum.
    """

    try:
        forum = Forum.objects.get(slug=forum_slug)
    except Forum.DoesNotExist:
        raise Http404

    threads = forum.thread_set.all()

    return jingo.render(request, 'threads.html',
                        {'forum': forum, 'threads': threads})


def posts(request, forum_slug, thread_id):
    """
    View all the posts in a thread.
    """

    try:
        forum = Forum.objects.get(slug=forum_slug)
    except Forum.DoesNotExist:
        raise Http404

    try:
        thread = Thread.objects.get(pk=thread_id)
    except Thread.DoesNotExist:
        raise Http404

    posts = thread.post_set.all()

    form = ReplyForm({'thread': thread.id, 'author': request.user.id})

    return jingo.render(request, 'posts.html',
                        {'forum': forum, 'thread': thread,
                         'posts': posts, 'form': form})


def reply(request):

    form = ReplyForm(request.POST)

    if form.is_valid():
        post = form.save()
        thread = Thread.objects.get(pk=request.POST.get('thread'))
        return HttpResponseRedirect(
            reverse('forums.posts',
                    kwargs={'forum_slug': thread.forum.slug,
                            'thread_id': thread.id}))

    return jingo.render(request, 'bad_reply.html')


def new_thread(request, forum_slug):
    """Start a new thread."""

    try:
        forum = Forum.objects.get(slug=forum_slug)
    except Forum.DoesNotExist:
        raise Http404

    if request.method == 'GET':
        form = NewThreadForm({'forum': forum.id})
        return jingo.render(request, 'new_thread.html',
                            {'form': form, 'forum': forum})

    form = NewThreadForm(request.POST)

    if form.is_valid():
        thread = form.save()
        return HttpResponseRedirect(
            reverse('forums.posts',
                    kwargs={'forum_slug': thread.forum.slug,
                            'thread_id': thread.id}))

    return jingo.render(request, 'bad_reply.html')
