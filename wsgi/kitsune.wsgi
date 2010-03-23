import os
import site

import django.core.handlers.wsgi

# Add the parent dir to the python path so we can import manage
wsgidir = os.path.dirname(__file__)
site.addsitedir(os.path.abspath(os.path.join(wsgidir, '../../')))

# kitsune.manage adds the `apps` and `lib` directories to the path
import kitsune.manage

# for mod-wsgi
application = django.core.handlers.wsgi.WSGIHandler()
