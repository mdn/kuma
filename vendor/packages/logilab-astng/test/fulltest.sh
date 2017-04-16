#!/bin/sh

if [ $@ ] ; then
    PYVERSIONS=$@
else
    PYVERSIONS="2.3 2.4 2.5 2.6"
fi
PYTEST=`which pytest`
for ver in $PYVERSIONS; do  
    echo "@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@"
    echo `python$ver -V`
    echo "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
    python$ver $PYTEST
    echo "^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^"
    echo `python$ver -V` -OO
    python$ver -OO $PYTEST
done
