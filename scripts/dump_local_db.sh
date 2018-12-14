#!/bin/bash

set -e

#################
# Setup Variables
#################

if [ -z "$DATABASE_URL" ]; then
    echo "DATABASE_URL must be a valid connection URL. Are you in the docker environment?"
    exit 1
fi

# Parse DATABASE_URL for database connection parts
# DATABASE_URL=mysql://root:kuma@mysql:3306/developer_mozilla_org
DB_NAME=${DATABASE_URL##*/}      # Name is after final slash
DB_URL_BASE=${DATABASE_URL%/*}   # Everything except the name
DB_PORT=${DB_URL_BASE##*:}       # Capture port (3306)
DB_TMP=${DB_URL_BASE%:*}         # Drop :3306 and...
DB_TMP=${DB_TMP#*://}            # Drop mysql://
DB_USER=${DB_TMP%:*}             # Capture user (root)
DB_TMP=${DB_TMP#*:}              # Drop user
DB_PASSWORD=${DB_TMP%@*}         # Capture password (kuma)
DB_HOST=${DB_TMP#*@}             # Capture hostname (mysql)


echo "*** Exporting to ${DB_NAME}.sql"
# Export to SQL file
mysqldump --host=$DB_HOST --user=$DB_USER --password=$DB_PASSWORD \
  $DB_NAME > ${DB_NAME}.sql
echo "*** Compressing to ${DB_NAME}.sql.gz"
gzip ${DB_NAME}.sql
