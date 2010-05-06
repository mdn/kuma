from tower import ugettext_lazy as _lazy
from .utils import crc32
from .sphinxapi import (SPH_SORT_ATTR_DESC, SPH_SORT_ATTR_ASC,
                        SPH_SORT_EXTENDED, SPH_GROUPBY_ATTR)


WHERE_WIKI = 1
WHERE_SUPPORT = 2
WHERE_BASIC = WHERE_WIKI | WHERE_SUPPORT
WHERE_DISCUSSION = 4

# Forum status constants
STATUS_STICKY = crc32('s')
STATUS_PROPOSED = crc32('p')
STATUS_REQUEST = crc32('r')
STATUS_NORMAL = crc32('n')
STATUS_ORIGINALREPLY = crc32('g')
STATUS_HOT = crc32('h')
STATUS_ANNOUNCE = crc32('a')
STATUS_INVALID = crc32('i')
STATUS_LOCKED = crc32('l')
STATUS_ARCHIVE = crc32('v')
STATUS_SOLVED = crc32('o')

# aliases
STATUS_ALIAS_NO = 0
STATUS_ALIAS_NR = 91
STATUS_ALIAS_NH = 92
STATUS_ALIAS_HA = 93
STATUS_ALIAS_SO = 94
STATUS_ALIAS_AR = 95
STATUS_ALIAS_OT = 96

# list passed to django forms
STATUS_LIST = (
    (STATUS_ALIAS_NO, _lazy(u"Don't filter")),
    (STATUS_ALIAS_NR, _lazy(u'Has no replies')),
    (STATUS_ALIAS_NH, _lazy(u'Needs help')),
    (STATUS_ALIAS_HA, _lazy(u'Has an answer')),
    (STATUS_ALIAS_SO, _lazy(u'Solved')),
    (STATUS_ALIAS_AR, _lazy(u'Archived')),
    (STATUS_ALIAS_OT, _lazy(u'Other')),
)
# reverse lookup
STATUS_ALIAS_REVERSE = {
    STATUS_ALIAS_NO: (),
    STATUS_ALIAS_NH: (STATUS_NORMAL, STATUS_ORIGINALREPLY),
    STATUS_ALIAS_HA: (STATUS_PROPOSED, STATUS_REQUEST),
    STATUS_ALIAS_SO: (STATUS_SOLVED,),
    STATUS_ALIAS_AR: (STATUS_ARCHIVE,),
    STATUS_ALIAS_OT: (STATUS_LOCKED, STATUS_STICKY, STATUS_ANNOUNCE,
        STATUS_INVALID, STATUS_HOT,),
}

DATE_NONE = 0
DATE_BEFORE = 1
DATE_AFTER = 2

DATE_LIST = (
    (DATE_NONE, _lazy(u"Don't filter")),
    (DATE_BEFORE, _lazy(u'Before')),
    (DATE_AFTER, _lazy(u'After')),
)

SORT = (
    #: (mode, clause)
    (SPH_SORT_EXTENDED, '@relevance DESC, age ASC'),  # default
    (SPH_SORT_ATTR_DESC, 'updated'),
    (SPH_SORT_ATTR_DESC, 'created'),
    (SPH_SORT_ATTR_DESC, 'replies'),
)

GROUPSORT = (
    '@relevance DESC, age ASC',  # default
    'updated DESC',
    'created DESC',
    'replies DESC',
)

# Integer values here map to tuples from SORT defined above
SORTBY_LIST = (
    (0, _lazy(u'Relevance')),
    (1, _lazy(u'Last post date')),
    (2, _lazy(u'Original post date')),
    (3, _lazy(u'Number of replies')),
)

# For discussion forums
DISCUSSION_STICKY = 1
DISCUSSION_LOCKED = 2

DISCUSSION_STATUS_LIST = (
    (DISCUSSION_STICKY, _lazy(u'Sticky')),
    (DISCUSSION_LOCKED, _lazy(u'Locked')),
)
