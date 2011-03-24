#!/bin/bash

cd /vagrant

mkdir -m0777 -p media/uploads
/usr/bin/python2.6 ./manage.py syncdb --noinput
/usr/bin/python2.6 ./manage.py createsuperuser --username=admin --email=lorchard@mozilla.com --noinput

# Force admin password to 'admin'
/usr/bin/mysql -ukuma -pkuma -e"UPDATE auth_user SET password='sha1$b0273$3c1e98ab1537b85b5b81ea725dc16bc657d410dd' WHERE username='admin'" kuma

/usr/bin/python2.6 ./manage.py update_product_details
/usr/bin/python2.6 ./manage.py update_feeds
