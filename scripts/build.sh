#!/bin/bash
# This script should run from inside Hudson

cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build..."

# Clean up after last time.
find . -name '*.pyc' | xargs rm

if [ ! -d "$VENV/bin" ]; then
    echo "No virtualenv found; making one..."
    virtualenv --no-site-packages $VENV
fi

source $VENV/bin/activate

pip install -qr requirements-dev.txt

cat > settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = 'workspace.urls'
LOG_LEVEL = logging.ERROR
DATABASES['default']['TEST_CHARSET'] = 'utf8'
DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'
DICT_DIR='/usr/local/share/myspell/'
SETTINGS

echo "Starting tests..."
export FORCE_DB=1
coverage run manage.py test --noinput --logging-clear-handlers --with-xunit
coverage xml $(find apps lib -name '*.py')

echo 'Booyahkasha!'
