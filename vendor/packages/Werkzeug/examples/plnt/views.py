# -*- coding: utf-8 -*-
"""
    plnt.views
    ~~~~~~~~~~

    Display the aggregated feeds.

    :copyright: (c) 2009 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD.
"""
from datetime import datetime, date
from plnt.database import Blog, Entry
from plnt.utils import Pagination, expose, render_template


#: number of items per page
PER_PAGE = 30


@expose('/', defaults={'page': 1})
@expose('/page/<int:page>')
def index(request, page):
    """Show the index page or any an offset of it."""
    days = []
    days_found = set()
    query = Entry.query.order_by(Entry.pub_date.desc())
    pagination = Pagination(query, PER_PAGE, page, 'index')
    for entry in pagination.entries:
        day = date(*entry.pub_date.timetuple()[:3])
        if day not in days_found:
            days_found.add(day)
            days.append({'date': day, 'entries': []})
        days[-1]['entries'].append(entry)
    return render_template('index.html', days=days, pagination=pagination)


@expose('/about')
def about(request):
    """Show the about page, so that we have another view func ;-)"""
    return render_template('about.html')
