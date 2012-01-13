#!/bin/bash
# 
# HACK: Run the migration command on chunks until it runs out.
#
# Since the migration process eats up memory without end, run migration on
# limited chunks in a loop. If a migration run comes up with a non-zero
# exit status, then presumably there's nothing left to migrate and so the loop
# can stop.
#
while [ 1 ]; do
    ./manage.py migrate_to_kuma_wiki --all --limit=200
    if [ $? -ne 0 ]; then
        break
    fi
done
