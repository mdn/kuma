# This script should be called from within Hudson
cd $WORKSPACE
VENV=$WORKSPACE/venv
VENDOR=$WORKSPACE/vendor
LOCALE=$WORKSPACE/locale

echo "Starting build on executor $EXECUTOR_NUMBER..." `date`

echo "Setup..." `date`

# Make sure there's no old pyc files around.
find . -name '*.pyc' | xargs rm

if [ ! -d "$VENV/bin" ]; then
  echo "No virtualenv found.  Making one..."
  virtualenv $VENV
fi

echo "Activating $VENV"
source $VENV/bin/activate

pip install -q -r requirements/compiled.txt

# Create paths we want for addons
if [ ! -d "$LOCALE" ]; then
    echo "No locale dir?  Cloning..."
    svn co http://svn.mozilla.org/projects/mdn/trunk/locale $LOCALE
    #git clone --recursive git://github.com/fwenzel/mdn-locales.git $LOCALE
fi

if [ ! -d "$VENDOR" ]; then
    echo "No vendor lib?  Cloning..."
    git clone --recursive git://github.com/mozilla/kuma-lib.git $VENDOR
fi

# Update the vendor lib.
echo "Updating vendor..."
pushd $VENDOR && git pull origin master && git submodule sync && git submodule update --init;
popd

python manage.py update_product_details

cat > settings_local.py <<SETTINGS
from settings import *
ROOT_URLCONF = '%s.urls' % ROOT_PACKAGE
LOG_LEVEL = logging.ERROR
DATABASES['default']['HOST'] = 'sm-hudson01'
DATABASES['default']['USER'] = 'hudson'
DATABASES['default']['TEST_NAME'] = 'test_kuma'
DATABASES['default']['TEST_CHARSET'] = 'utf8'
DATABASES['default']['TEST_COLLATION'] = 'utf8_general_ci'
CACHE_BACKEND = 'caching.backends.locmem://'

ASYNC_SIGNALS = False
SETTINGS


echo "Starting tests..." `date`
export FORCE_DB='yes sir'

# with-coverage excludes sphinx so it doesn't conflict with real builds.
if [[ $2 = 'with-coverage' ]]; then
    coverage run manage.py test -v 2 --noinput --logging-clear-handlers --with-xunit
    coverage xml $(find apps lib -name '*.py')
else
    python manage.py test actioncounters contentflagging dekicompat demos devmo -v 2 --noinput --logging-clear-handlers --with-xunit
fi

echo 'shazam!'
