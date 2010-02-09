# Create your views here.

from .clients import *
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

    where = int(request.GET.get('w', WHERE_ALL))

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

    return render_to_response('search/results.html',{'results':results,'q':q,})

