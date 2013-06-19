from django.shortcuts import render
from django.views.decorators.http import require_GET
from waffle.decorators import waffle_flag

from wiki.models import Document

from . import (DEFAULT_LOCALE, ORDERS, LOCALES, TOPICS, LANGUAGES,
               WAFFLE_FLAG)


@require_GET
@waffle_flag(WAFFLE_FLAG)
def index(request):
    locale = request.GET.get('locale')
    topic = request.GET.get('topic')
    orderby = request.GET.get('orderby')
    localization_flags = request.GET.get('localization_flags')

    docs = Document.objects.exclude(locale=DEFAULT_LOCALE)

    if locale and locale in LANGUAGES:
        docs = docs.filter(locale=locale)

    if localization_flags:
        docs = docs.filter(current_revision__localization_tags__name=localization_flags)

    if orderby and orderby in ORDERS:
        docs = docs.order_by('-' + orderby)
    else:
        docs = docs.order_by('-modified')

    filters = {
        'locale': locale,
        'topic': topic,
        'localization_flags': localization_flags,
        'orderby': orderby,
    }

    params = {
        'locales': LOCALES, 'topics': TOPICS, 'orderby_list': ORDERS,
        'docs': docs, 'filters': filters,
    }
    return render(request, 'l10ndashboard/home.html', params)
