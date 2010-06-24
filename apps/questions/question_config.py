from tower import ugettext_lazy as _

products = [
    {
        'key': 'desktop',
        'name': _('Firefox on desktop'),
        'extra_fields': ['troubleshooting', 'ff_version', 'os', 'plugins'],
        'categories': [
        {
            'key': 'd1',
            'name': _('Firefox is having problems with certain web sites'),
            'extra_fields': ['sites_affected'],
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        },
        {
            'key': 'd2',
            'name': _('Firefox is crashing or closing unexpectedly'),
            'extra_fields': ['crash_id'],
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        },
        {
            'key': 'd3',
            'name': _('I have a problem with my bookmarks, cookies, history or settings'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        },
        {
            'key': 'd4',
            'name': _('I have a problem with an extension, plugin or with Thunderbird'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        },
        {
            'key': 'd5',
            'name': _('I have feedback about Firefox or would like a new feature'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        },
        {
            'key': 'd6',
            'name': _('I have another kind of problem with Firefox'),
            'extra_fields': ['frequency', 'started'],
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
        },
    ]
    },
    {
        'key': 'mobile',
        'name': _('Firefox on mobile'),
        'extra_fields': ['ff_version', 'os', 'plugins'],
        'categories': [
            {
                'key': 'm1',
                'name': _('Firefox is very slow on my phone lorem ipsum'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            },
            {
                'key': 'm2',
                'name': _('Lorem ipsum dolor sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            },
        ]
    },
    {
        'key': 'home',
        'name': _('Firefox Home app for iPhone'),
        'categories': [
            {
                'key': 'i1',
                'name': _('Firefox Home crashes my iPhone sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            },
            {
                'key': 'i2',
                'name': _('Lorem ipsum dolor sit amet'),
                'articles': [
                    {'title': 'Article lorem ipsum 1', 'url': '#'},
                    {'title': 'Article lorem ipsum 2', 'url': '#'},
                    {'title': 'Article lorem ipsum 3', 'url': '#'},
                ]
            },
        ]
    },
    {
        'key': 'other',
        'name': _('Not a Firefox product'),
        'categories': [
            {
            'key': 'o1',
            'name': _('Lorem ipsum dolor sit amet'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
            ]
            },
            {
            'key': 'o2',
            'name': _('Lorem ipsum dolor sit amet'),
            'articles': [
                {'title': 'Article lorem ipsum 1', 'url': '#'},
                {'title': 'Article lorem ipsum 2', 'url': '#'},
                {'title': 'Article lorem ipsum 3', 'url': '#'},
            ]
            },
        ]
    },
]
