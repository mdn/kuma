""" A script to extract raw and rendered versions of all documents in the db

This script extracts documents from the db into a testdocs/ directory.
It is intended for creating a test corpus and verifying that changes
to kuma and/or kumascript do not cause rendering changes to the documents.

In order to make it work it may be necessary to modify the KUMASCRIPT_TIMEOUT
setting in kuma/settings/common.py to be at least 60 seconds
"""

import json
import os
import os.path
import sys
from datetime import datetime

# Adjust the path so the imports below all work.
sys.path[0] = os.path.dirname(os.path.dirname(os.path.realpath(__file__)))

import django
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'kuma.settings.testing')
django.setup()

import kuma.wiki.models
import kuma.wiki.kumascript

args = sys.argv[1:];
if len(args) > 0:
    docs = [kuma.wiki.models.Document.from_url('http://localhost:8000/' + a) for a in args]
else:
    docs = kuma.wiki.models.Document.objects.all()

for d in docs:
    path = d.get_absolute_url()[1:]  + '.html' # strip off the leading /
    rawfilename = os.path.join('./testdocs', path)
    rawdirname = os.path.dirname(rawfilename)
    if not os.path.exists(rawdirname):
        os.makedirs(rawdirname)

    print "writing {}: {}".format(rawfilename, len(d.html))
    with open(rawfilename, 'w') as f:
        f.write(d.html.encode('utf-8'))

    start = datetime.now()
    try:
        #rendered, errors = d.get_rendered()
        rendered, errors = kuma.wiki.kumascript.get(d, None, timeout=120)
        end = datetime.now()
        print "got rendered doc in: {}s".format(end-start)
    except Exception as e:
        print "writing rendering exception: {}".format(e)
        with open(rawfilename + ".exception", 'w') as f:
            f.write(str(e).encode('utf-8'))
        rendered = ""

    if errors:
        print "writing errors for: {}".format(path)
        with open(rawfilename + ".errors", 'w') as f:
            f.write(json.dumps(errors).encode('utf-8'))

    if rendered:
        print "writing {}: {}".format(rawfilename + ".rendered", len(rendered))
        with open(rawfilename + ".rendered", 'w') as f:
            f.write(rendered.encode('utf-8'))
