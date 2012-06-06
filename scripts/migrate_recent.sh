#!/bin/bash
# Script for staging server migration cron job
# Migrate the 50 most recently modified MindTouch pages 

python2.6 manage.py migrate_to_kuma_wiki --recent=50
