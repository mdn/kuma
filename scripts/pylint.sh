#!/bin/bash
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

VENV=$WORKSPACE/venv
source $VENV/bin/activate
export PYTHONPATH="$WORKSPACE/..:$WORKSPACE/apps:$WORKSPACE/lib"
pylint --rcfile scripts/pylintrc $WORKSPACE > pylint.txt
echo "pylint complete"
