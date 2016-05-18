We are using English strings for gettext message ids.

Instructions:
1) ./manage.py extract
2) ./manage.py merge
Optional:
3) locale/compile-mo.sh locale


New Locales:
Assuming you want to add the locale 'xx':
1) make locale LOCALE=xx
