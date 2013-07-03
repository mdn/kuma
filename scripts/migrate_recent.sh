#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

# Script for staging server migration cron job
# Migrate the 50 most recently modified MindTouch pages 

python2.6 manage.py migrate_to_kuma_wiki --recent=50
