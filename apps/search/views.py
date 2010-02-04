# Create your views here.

from .client import Client
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
import datetime
from .utils import crc32

WHERE_WIKI = 1
WHERE_FORUM = 2
WHERE_ALL = WHERE_WIKI | WHERE_FORUM

def search(request):
    q = request.GET.get('q','search')

    locale = request.GET.get('locale',request.LANGUAGE_CODE)

    client = Client()

    where = int(request.GET.get('w', WHERE_ALL))

    results = []

    if (where & WHERE_WIKI):
        category = [ int(i) for i in request.GET.get('category','1,17,18').split(',') ]
        if request.GET.get('tag'):
            tag = [ crc32(t) for t in request.GET.get('tag').split(',') ]
        else:
            tag = []
        results += client.search_wiki(q,locale,{'category':category,'tag':tag})
    
    if (where & WHERE_FORUM):
        forums = [ int(i) for i in request.GET.get('forums','1').split(',') ]
        
        results += client.search_forum(q, {'forumId':forums})

    return render_to_response('search/results.html',{'results':results,'q':q,})

