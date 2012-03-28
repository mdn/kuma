#!/bin/bash
# Script for staging server migration cron job
# Migrate most-viewed, recently-updated, longest, and non-english pages

python26 manage.py migrate_to_kuma_wiki --wipe --viewed=50 --recent=50 --longest=50 --nonen=50
