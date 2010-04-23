import jingo

from .models import Forum, Thread, Post


def forums(request):
    """
    View all the forums.
    """
    return jingo.render(request, 'forums.html')


def threads(request):
    """
    View all the threads in a forum.
    """
    return jingo.render(request, 'threads.html')


def posts(request):
    """
    View all the posts in a thread.
    """
    return jingo.render(request, 'posts.html')
