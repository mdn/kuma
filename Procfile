web: find kuma -name '*.pyc' -exec rm {} \; && python2.6 manage.py runserver 0.0.0.0:8000
worker: python2.6 manage.py celery worker --events --beat --autoreload --concurrency=4
camera: python2.6 manage.py celerycam --freq=2.0
kumascript: node kumascript/run.js
