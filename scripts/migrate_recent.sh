#!/bin/bash
#
# Migrate the 25 most recently modified MindTouch pages 
#
./manage.py migrate_to_kuma_wiki --recent=25
