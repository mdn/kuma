from .utils import crc32

# TODO: use lazy gettext, as in zamboni
from django.utils.translation import ugettext

WHERE_WIKI = 1
WHERE_FORUM = 2
WHERE_ALL = WHERE_WIKI | WHERE_FORUM

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
    (STATUS_ALIAS_NO, ugettext('Don\'t filter')),
    (STATUS_ALIAS_NR, ugettext('Has no replies')),
    (STATUS_ALIAS_NH, ugettext('Needs help')),
    (STATUS_ALIAS_HA, ugettext('Has an answer')),
    (STATUS_ALIAS_SO, ugettext('Solved')),
    (STATUS_ALIAS_AR, ugettext('Archived')),
    (STATUS_ALIAS_OT, ugettext('Other')),
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

CREATED_NONE = 0
CREATED_BEFORE = 1
CREATED_AFTER = 2

CREATED_LIST = (
    (CREATED_NONE, ugettext('Don\'t filter')),
    (CREATED_BEFORE, ugettext('Before')),
    (CREATED_AFTER, ugettext('After')),
)

# multiplier
LUP_MULTIPLIER = 86400 # one day
LUP_LIST = (
    (0, "Don't filter"),
    (1, "Last 24 hours"),
    (7, "Last week"),
    (30, "Last month"),
    (180, "Last 6 months"),
)

# sort by constants
SORTBY_RELEVANCE = 0
SORTBY_LASTMODIF = 2
SORTBY_CREATED = 3
SORTBY_REPLYCOUNT = 4

SORTBY_LIST = (
    (SORTBY_RELEVANCE, ugettext("Relevance")),
    (SORTBY_LASTMODIF, ugettext("Last post date")),
    (SORTBY_CREATED, ugettext("Original post date")),
    (SORTBY_REPLYCOUNT, ugettext("Number of replies")),
)

# set this to the value of SPH_SORT_*
SORTBY_MODE = 1 # SPH_SORT_ATTR_DESC
