# Create your views here.

from .client import Client
from django.shortcuts import render_to_response
from django.http import Http404, HttpResponseRedirect
from django.template import RequestContext
from django.core.urlresolvers import reverse
import datetime

WHERE_WIKI = 1
WHERE_FORUM = 2
WHERE_ALL = WHERE_WIKI | WHERE_FORUM

def search(request):
    q = request.GET.get('q','search')

    locale = request.LANGUAGE_CODE

    client = Client()

    where = request.GET.get('w', WHERE_ALL)

    results = []

    if (where & WHERE_WIKI):
        results += client.search_wiki(q,locale)
    
    if (where & WHERE_FORUM):
        results += client.search_forum(q)

    return render_to_response('search/results.html',{'results':results,'q':q})

