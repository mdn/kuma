from tower import ugettext_lazy as _


class SECTION_ADDONS:
    short = 'addons'
    pretty = _(u'Add-ons')
    twitter = 'twitter-addons'
    updates = 'updates-addons'


class SECTION_APPS:
    short = 'mozilla'
    pretty = _(u'Mozilla')
    twitter = 'twitter-mozilla'
    updates = 'updates-mozilla'


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


SECTION_USAGE = _sections = (SECTION_WEB, SECTION_MOBILE, SECTION_ADDONS,
                             SECTION_APPS)

SECTIONS = dict((section.short, section)
                for section in _sections)

SECTIONS_TWITTER = dict((section.twitter, section)
                        for section in _sections)

SECTIONS_UPDATES = dict((section.updates, section)
                        for section in _sections)

INTEREST_SUGGESTIONS = ["audio", "canvas", "css3", "device", "files", "fonts",
    "forms", "geolocation", "javascript", "html5", "indexeddb", "dragndrop",
    "mobile", "offlinesupport", "svg", "video", "webgl", "websockets",
    "webworkers", "xhr", "multitouch", ]
