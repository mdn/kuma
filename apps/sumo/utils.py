from django.core import paginator

from flatqs import flatten


def paginate(request, queryset, per_page=20):
    """Get a Paginator, abstracting some common paging actions."""
    p = paginator.Paginator(queryset, per_page)

    # Get the page from the request, make sure it's an int.
    try:
        page = int(request.GET.get('page', 1))
    except ValueError:
        page = 1

    # Get a page of results, or the first page if there's a problem.
    try:
        paginated = p.page(page)
    except (paginator.EmptyPage, paginator.InvalidPage):
        paginated = p.page(1)

    base = request.build_absolute_uri(request.path)
    request_copy = request.GET.copy()
    try:
        del request_copy['page']
    except KeyError:
        pass
    paginated.url = u'%s?%s' % (base, flatten(request_copy, encode=False))
    return paginated
