from django.http import Http404, HttpResponseRedirect
from django.shortcuts import get_object_or_404

import jingo

from sumo.urlresolvers import reverse
from sumo.utils import paginate
from .models import Forum, Thread
from .forms import ReplyForm, NewThreadForm
import forums as constants


def forums(request):
    """
    View all the forums.
    """

    forums = paginate(request, Forum.objects.all())

    return jingo.render(request, 'forums.html', {'forums': forums})


def sort_threads(threads, sort=0, desc=0):
    if desc:
        prefix = '-'
    else:
        prefix = ''

    if sort == 3:
        return threads.order_by(prefix + 'creator__username').all()
    elif sort == 4:
        return threads.order_by(prefix + 'replies').all()
    elif sort == 5:
        return threads.order_by(prefix + 'last_post__created').all()

    # If nothing matches, use default sorting
    return threads.all()


def threads(request, forum_slug):
    """
    View all the threads in a forum.
    """

    try:
        forum = Forum.objects.get(slug=forum_slug)
    except Forum.DoesNotExist:
        raise Http404

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

    return jingo.render(request, 'threads.html',
                        {'forum': forum, 'threads': threads_,
                         'sort': sort, 'desc_toggle': desc_toggle})


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

    posts_ = paginate(request, thread.post_set.all(),
                      constants.POSTS_PER_PAGE)

    form = ReplyForm({'thread': thread.id, 'author': request.user.id})

    return jingo.render(request, 'posts.html',
                        {'forum': forum, 'thread': thread,
                         'posts': posts_, 'form': form})


def reply(request, forum_slug, thread_id):

    form = ReplyForm(request.POST)

    if form.is_valid():
        form.save()
        thread = Thread.objects.get(pk=request.POST.get('thread'))

        # TODO: This should not need to be in the view.
        thread.replies += 1
        thread.save()
        return HttpResponseRedirect(
            reverse('forums.posts',
                    kwargs={'forum_slug': thread.forum.slug,
                            'thread_id': thread.id}))

    return jingo.render(request, 'bad_reply.html')


def new_thread(request, forum_slug):
    """Start a new thread."""

    # TODO: Once we can log in through Kitsune, use reverse here.
    if not request.user.is_authenticated():
        return HttpResponseRedirect('/tiki-login.php')

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
