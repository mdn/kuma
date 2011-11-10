# This script should be called from within Hudson
DB=test_$JOB_NAME
echo "Using database: $DB"
cd $WORKSPACE
VENV=$WORKSPACE/venv
VENDOR=$WORKSPACE/vendor
LOCALE=$WORKSPACE/locale

echo "Starting build on executor $EXECUTOR_NUMBER..." `date`
echo "Setup..." `date`

# Make sure there's no old pyc files around.
find . -name '*.pyc' | xargs rm

# virtualenv - create if necessary
if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV
fi
echo "Activating $VENV"
source $VENV/bin/activate

pip install -q -r requirements/compiled.txt

# locale - create if necessary
if [ ! -d "$LOCALE" ]; then
    echo "No locale dir?  Cloning..."
    svn co http://svn.mozilla.org/projects/mdn/trunk/locale $LOCALE
fi

# vendor - create if necessary
if [ ! -d "$VENDOR" ]; then
    echo "No vendor lib?  Cloning..."
    git clone --recursive git://github.com/mozilla/kuma-lib.git $VENDOR
fi
# Update the vendor lib.
echo "Updating vendor..."
pushd $VENDOR && git pull origin master && git submodule sync && git submodule update --init;
popd

# product details - create if necessary
if [ ! -d "$WORKSPACE/../product_details_json" ]; then
    mkdir $WORKSPACE/../product_details_json
fi
python manage.py update_product_details

# create settings_local.py
cat > settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE
LOG_LEVEL = logging.ERROR
DATABASES['default']['HOST'] = 'localhost'
DATABASES['default']['USER'] = 'hudson'
DATABASES['default']['TEST_NAME'] = '$DB'
DATABASES['default']['TEST_CHARSET'] = 'utf8'
DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'
CACHE_BACKEND = 'caching.backends.locmem://'

ASYNC_SIGNALS = False

NOSE_PLUGINS = [
    'nose.plugins.logcapture.LogCapture',
    'nose.plugins.xunit.Xunit',
]
NOSE_ARGS = [
    '--logging-clear-handlers',
    '--with-xunit',
]
SETTINGS


echo "Starting tests..." `date`
export FORCE_DB='yes sir'

# with-coverage excludes sphinx so it doesn't conflict with real builds.
if [[ $2 = 'with-coverage' ]]; then
    coverage run manage.py test actioncounters contentflagging dekicompat demos devmo landing users -v 2 --noinput
    coverage xml $(find apps lib -name '*.py')
else
    python manage.py test actioncounters contentflagging dekicompat demos devmo landing users -v 2 --noinput
fi

echo 'shazam!'
