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

PYTHON26=`which python26`
if [ -z "$PYTHON26" ]; then
    ln -s $VENV/bin/python $VENV/bin/python26
fi

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
    '--traverse-namespace',  # needed for finding tests under the kuma namespace
]
ES_INDEX_PREFIX = 'mdn_$JOB_NAME'
ES_URLS = ['http://jenkins-es20:9200']
ES_INDEXES = {'default': 'main_index'}
ES_INDEXING_TIMEOUT = 30
ES_LIVE_INDEX = True
ES_DISABLED = False

SETTINGS


echo "Starting tests..." `date`
export FORCE_DB='yes sir'

if [[ $1 = '--with-coverage' ]]; then
    coverage run manage.py test actioncounters contentflagging dashboards demos devmo kpi landing search users wiki -v 2 --noinput
    coverage xml $(find apps/actioncounters apps/contentflagging apps/dashboards apps/demos apps/devmo apps/kpi apps/landing apps/search apps/users apps/wiki lib -name '*.py')
else
    python manage.py test actioncounters contentflagging dashboards demos devmo kpi landing search users wiki -v 2 --noinput
fi
echo "tests complete" `date`

pip install pep8
echo "Starting pep8..." `date`
pep8 apps/ > pep8_report.txt
echo "pep8 complete" `date`

pip install pylint
echo "Starting pylint..." `date`
find apps/ -iname "*.py" | xargs pylint -f parseable > pylint_report.txt
echo "pylint complete" `date`

echo 'shazam!'
