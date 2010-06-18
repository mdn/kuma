from django.utils.datastructures import SortedDict

from tower import ugettext_lazy as _

products = SortedDict([
    ('desktop', {
        'name': _('Firefox on desktop'),
        'extra_fields': ['troubleshooting', 'ff_version', 'os', 'plugins'],
        'categories': SortedDict([
        ('d1', {
            'name': _('Firefox is having problems with certain web sites'),
            'extra_fields': ['sites_affected'],
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        }),
        ('d2', {
            'name': _('Firefox is crashing or closing unexpectedly'),
            'extra_fields': ['crash_id'],
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        }),
        ('d3', {
            'name': _('I have a problem with my bookmarks, cookies, history or settings'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        }),
        ('d4', {
            'name': _('I have a problem with an extension, plugin or with Thunderbird'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        }),
        ('d5', {
            'name': _('I have feedback about Firefox or would like a new feature'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        }),
        ('d6', {
            'name': _('I have another kind of problem with Firefox'),
            'extra_fields': ['frequency', 'started'],
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        }),
    ])
    }),
    ('mobile', {
        'name': _('Firefox on mobile'),
        'extra_fields': ['ff_version', 'os', 'plugins'],
        'categories': SortedDict([
            ('m1', {
                'name': _('Firefox is very slow on my phone lorem ipsum'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            }),
            ('m2', {
                'name': _('Lorem ipsum dolor sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            }),
        ])
    }),
    ('home', {
        'name': _('Firefox Home app for iPhone'),
        'categories': SortedDict([
            ('i1', {
                'name': _('Firefox Home crashes my iPhone sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            }),
            ('i2', {
                'name': _('Lorem ipsum dolor sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            }),
        ])
    }),
    ('other', {
        'name': _('Not a Firefox product'),
        'categories': SortedDict([
            ('o1', {
                'name': _('Lorem ipsum dolor sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                ]
            }),
            ('o2', {
                'name': _('Lorem ipsum dolor sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            }),
        ])
    }),
])

# Insert 'key' keys so we can go from product or category back to key:
for p_k, p_v in products.iteritems():
    p_v['key'] = p_k
    for c_k, c_v in p_v['categories'].iteritems():
        c_v['key'] = c_k
