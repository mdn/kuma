#!/bin/bash

set -e

#################
# Setup Variables
#################

# Directory of this script, default config
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PARENT_DIR="$( dirname ${DIR} )"
ETC_DIR="${PARENT_DIR}/etc"

if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL must be a valid connection URL. Are you in the docker environment?"
    exit 1
fi

# Parse DATABASE_URL for database connection parts
# DATABASE_URL=mysql://root:kuma@mysql:3306/developer_mozilla_org
DB_URL_BASE=${DATABASE_URL%/*}   # Remove database name from end
DB_PORT=${DB_URL_BASE##*:}       # Capture port (3306)
DB_TMP=${DB_URL_BASE%:*}         # Drop :3306 and...
DB_TMP=${DB_TMP#*://}            # Drop mysql://
DB_USER=${DB_TMP%:*}             # Capture user (root)
DB_TMP=${DB_TMP#*:}              # Drop user
DB_PASSWORD=${DB_TMP%@*}         # Capture password (kuma)
DB_HOST=${DB_TMP#*@}             # Capture hostname (mysql)

# Create a unique database with the current timestamp
DB_NAME=sample_$(date +%s)

# Setup parameters for sampling
VERBOSITY=${VERBOSITY:-2}
SAMPLE_HOST=${SAMPLE_HOST:-developer.mozilla.org}
SAMPLE_SSL=${SAMPLE_SSL:-1}
SAMPLE_DUMP="mdn_sample_db.sql"
SAMPLE_SPEC=${1:-${ETC_DIR}/sample_db.json}
SAMPLE_DEBUG=${SAMPLE_DEBUG:-0}
if [ "$SAMPLE_DEBUG" == "0" ]; then
    DEBUG_CMD=
else
    DEBUG_CMD="python -m pdb"
fi

SAMPLE_ARGS=""
if [ "$SAMPLE_HOST" != "developer.mozilla.org" ]; then
    SAMPLE_ARGS="$SAMPLE_ARGS --host=$SAMPLE_HOST"
fi

if [ "$SAMPLE_SSL" == "0" ]; then
    SAMPLE_ARGS="$SAMPLE_ARGS --nossl"
fi

# Use the new database in Django management commands
export DATABASE_URL=${DB_URL_BASE}/${DB_NAME}

#############
# Import data
#############

echo "*** Creating the sample database ${DB_NAME}"
mysql --host=$DB_HOST --user=$DB_USER --password=$DB_PASSWORD \
  -e "CREATE DATABASE ${DB_NAME} CHARACTER SET utf8;"

echo "*** Initializing the database"
$DIR/../manage.py migrate

echo "*** Importing data from ${SAMPLE_HOST}"
$DEBUG_CMD $DIR/../manage.py sample_mdn $SAMPLE_ARGS -v$VERBOSITY $SAMPLE_SPEC

echo "*** Fetching Hacks Posts"
$DIR/../manage.py update_feeds

echo "*** Exporting to ${SAMPLE_DUMP}"
# Export to SQL file
mysqldump --host=$DB_HOST --user=$DB_USER --password=$DB_PASSWORD \
  $DB_NAME > ${SAMPLE_DUMP}

echo "*** Dropping sample database ${DB_NAME}"
mysql --host=$DB_HOST --user=$DB_USER --database=${DB_NAME} \
  --password=$DB_PASSWORD \
  -e "DROP DATABASE ${DB_NAME};"
