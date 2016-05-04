web: gunicorn kuma.wsgi -w 2 -b 0.0.0.0:8000
worker: python2.7 manage.py celery worker --events --beat --autoreload --concurrency=4 -Q mdn_purgeable,mdn_search,mdn_emails,mdn_wiki,celery
camera: python2.7 manage.py celerycam --freq=2.0
kumascript: node kumascript/run.js
stylus: scripts/compile-stylesheets --watch
