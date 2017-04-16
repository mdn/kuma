#!/bin/sh

# The translate toolkit must be in your PYTHONPATH when you
# build these documents.  Either install them or run:
#  . setpath
#
# The script will then find them, build docs and export them
# to sourceforge.
#
# You should also have a setup in .ssh/config that defines
# $sfaccount with your sourceforge shell login details for 
# the translate project.
#
# EPYDOC
# ======
# See: http://epydoc.sourceforge.net/manual-epytext.html
# and: http://epydoc.sourceforge.net/fields.html#fields

docdir=`dirname $0`
outputdir=$docdir/api/

rm -rf $outputdir
epydoc --config=$docdir/epydoc-config.ini --output=$outputdir


##To get the new documentation on SourceForge,
##create a new shell account and update the API docs

sfaccount=sftranslate-shell
#ssh $sfaccount create
#rsync -azv -e ssh --delete $outputdir $sfaccount:translate/htdocs/doc/api
