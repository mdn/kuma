from tower import ugettext_lazy as _


class SECTION_ADDONS:
    short = 'addons'
    pretty = _(u'Add-ons')
    twitter = 'twitter-addons'
    updates = 'updates-addons'


class SECTION_MOZILLA:
    short = 'mozilla'
    pretty = _(u'Mozilla')
    twitter = 'twitter-mozilla'
    updates = 'updates-mozilla'


class SECTION_APPS:
    short = 'apps'
    pretty = _(u'Apps')
    twitter = 'twitter-apps'
    updates = 'updates-apps'


class SECTION_MOBILE:
    short = 'mobile'
    pretty = _(u'Mobile')
    twitter = 'twitter-mobile'
    updates = 'updates-mobile'


class SECTION_WEB:
    short = 'web'
    pretty = _(u'Web')
    twitter = 'twitter-web'
    updates = 'updates-web'


class SECTION_HACKS:
    short = 'hacks'
    pretty = _(u'Moz Hacks')
    twitter = 'twitter-moz-hacks'
    updates = 'updates-moz-hacks'


SECTION_USAGE = _sections = (SECTION_HACKS,)

SECTIONS = dict((section.short, section)
                for section in _sections)

SECTIONS_TWITTER = dict((section.twitter, section)
                        for section in _sections)

SECTIONS_UPDATES = dict((section.updates, section)
                        for section in _sections)
