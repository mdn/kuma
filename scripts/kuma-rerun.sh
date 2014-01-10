#!/bin/bash

# Adapted from: https://gist.github.com/mythmon/4151152

export LEEROY_URL="https://leeroybot.herokuapp.com/"
LEEROY_RERUN="https://raw.github.com/lonnen/leeroy-rerun/master/leeroy-rerun.py"

# Usage
[[ -z $1 ]] && {
    echo "Rerun a Leeroy job for Kuma."
    echo -e "  $ $(basename $0) PULLNUM"
    exit 1
}

PULL=$1

python2 <(curl -s $LEEROY_RERUN) "https://github.com/mozilla/kuma/pull/${PULL}"
