We are using English strings for gettext message ids.

Instructions:
1) ./manage.py extract 
2) ./manage.py verbatimize --rename
   This will copy the POT files created in step 1 to templates/LC_MESSAGES
3) ./manage.py merge

Optional:
4) locale/compile-mo.sh locale

New Locales:
Assuming you want to add 'fr':
1) mkdir -p locale/fr/LC_MESSAGES
2) ./manage.py merge

or
1) msginit --no-translator -l fr -i templates/LC_MESSAGES/messages.pot -o fr/LC_MESSAGES/messages.po
2) repeat for other POT files
