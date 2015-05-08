# django 1.5 introduces force_text instead of force_unicode
try:
    from django.utils.encoding import force_text
except ImportError:
    from django.utils.encoding import force_unicode as force_text

# python 3.x does not have cPickle module
try:
    from cPickle import loads, dumps # cpython 2.x
except ImportError:
    from pickle import loads, dumps # cpython 3.x, other interpreters

# django 1.6 will deprecate django.utils.simple_json
try:
    import json
except ImportError:
    from django.utils import simplejson as json
    
