#!/bin/bash
# http://www.davidpashley.com/articles/writing-robust-shell-scripts/
set -u # Exit with error on unset variables
set -e # Exit with error if a command fails

# syntax:
# compile-mo.sh locale-dir/

function usage() {
    echo "syntax:"
    echo "compile.sh locale-dir/"
    exit 1
}

# check if file and dir are there
if [[ ($# -ne 1) || (! -d "$1") ]]; then usage; fi

for lang in `find $1 -type f -name "*.po"`; do
    dir=`dirname $lang`
    stem=`basename $lang .po`
    msgfmt --check-header -o ${dir}/${stem}.mo $lang
done
