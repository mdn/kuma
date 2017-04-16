from models import BlogPost
from django.template import RequestContext
from django.shortcuts import render_to_response
from django.http import Http404

def latest_post(request):
    try:
        post = BlogPost.objects.latest('date_posted')
    except BlogPost.DoesNotExist:
        raise Http404
    return render_to_response(
        'blog/latest_post.html', {'post' : post},
        context_instance = RequestContext(request)
    )