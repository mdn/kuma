web: python manage.py runserver 0.0.0.0:$PORT
worker: python manage.py celery worker --events --beat --autoreload --concurrency=4 -Q mdn_purgeable,mdn_search,mdn_emails,mdn_wiki,celery
camera: python manage.py celerycam --freq=2.0
