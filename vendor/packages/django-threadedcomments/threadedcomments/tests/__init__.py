from views_tests import *
from templatetags_tests import *
try:
    import comment_utils
except ImportError:
    pass
else:
    from moderator_tests import *
