# Create your views here.

import datetime

from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse

import jingo

from sumo.models import ForumThread, WikiPage

from .clients import ForumClient, WikiClient
from .utils import crc32
from sumo.models import *



WHERE_WIKI = 1
WHERE_FORUM = 2
WHERE_ALL = WHERE_WIKI | WHERE_FORUM

def search(request):
    q = request.GET.get('q','search')

    locale = (crc32(request.GET.get('locale',request.LANGUAGE_CODE)),)

    where = int(request.GET.get('w', WHERE_ALL))

    offset = int(request.GET.get('offset',0))

    results = []

    if (where & WHERE_WIKI):
        wc = WikiClient()
        category = map(int,request.GET.get('category','1,17,18').split(','))
        if request.GET.get('tag'):
            tag = map(crc32,request.GET.get('tag').split(','))
        else:
            tag = []
        results += wc.query(q,{'locale':locale,'category':category,'tag':tag})
    
    if (where & WHERE_FORUM):
        fc = ForumClient()
        forums = map(int,request.GET.get('forums','1').split(','))
        
        results += fc.query(q, {'forumId':forums})

    this_page = []
    for i in range(offset,offset+10):
        if results[i]['attrs'].get('category',False):
            this_page.append(WikiPage.objects.get(page_id=results[i]['id']))
        else:
            this_page.append(ForumThread.objects.get(threadId=results[i]['id']))

    return render_to_response('search/results.html',{'results':len(results),'this_page':this_page,'q':q,})

