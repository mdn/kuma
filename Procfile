web: find apps kuma -name '*.pyc' -exec rm {} \; && python2.6 manage.py runserver 0.0.0.0:8000
celery: python2.6 manage.py celeryd --events --beat --autoreload --concurrency=4
kumascript: node kumascript/run.js
stylus: scripts/compile-stylesheets --watch
