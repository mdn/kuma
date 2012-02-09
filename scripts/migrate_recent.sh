#!/bin/bash
# Script for staging server migration cron job
# Migrate the 25 most recently modified MindTouch pages 
#
python26 manage.py migrate_to_kuma_wiki --recent=25
