#!/bin/bash
# This script should run from inside Hudson

cd $WORKSPACE
VENV=$WORKSPACE/venv

echo "Starting build..."

if [ -z $1 ]; then
    echo "Warning: You should provide a unique name for this job to prevent database collisions."
    echo "Usage: ./build.sh <name>"
    echo "Continuing, but don't say you weren't warned."
fi

# Clean up after last time.
find . -name '*.pyc' -exec rm {} \;

if [ ! -d "$VENV/bin" ]; then
    echo "No virtualenv found; making one..."
    virtualenv --no-site-packages $VENV
fi

source $VENV/bin/activate

pip install -qUr requirements/dev.txt

python manage.py update_product_details

cat > settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = 'workspace.urls'
LOG_LEVEL = logging.ERROR
DATABASES['default']['NAME'] = 'kitsune_$1'
DATABASES['default']['TEST_NAME'] = 'test_kitsune_$1'
DATABASES['default']['TEST_CHARSET'] = 'utf8'
DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'
SETTINGS

echo "Starting tests..."
export FORCE_DB=1
coverage run manage.py test --noinput --logging-clear-handlers --with-xunit
coverage xml $(find apps lib -name '*.py')

echo 'Booyahkasha!'
