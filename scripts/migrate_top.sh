#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Script for staging server migration cron job
# Migrate most-viewed, recently-updated, longest, and non-english pages

python manage.py migrate_to_kuma_wiki --wipe --viewed=50 --recent=50 --longest=50 --nonen=50
