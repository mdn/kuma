# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.

SESSION=$USER

tmux has-session -t $SESSION
if [ $? -eq 0 ]; then
    echo "Session $SESSION already exists. Attaching."
    sleep 1
    tmux attach -t $SESSION
    exit 0;
fi

tmux new-session -d -s $SESSION

tmux split-window -t $SESSION:0 -v -p 50 './manage.py celeryd; /bin/bash'
tmux swap-pane    -t $SESSION:0 -U
tmux split-window -t $SESSION:0 -v -p 50 './manage.py runserver 0.0.0.0:8000; /bin/bash'
tmux swap-pane    -t $SESSION:0 -U
tmux split-window -t $SESSION:0 -v -p 50 'node kumascript/run.js; /bin/bash'
tmux select-pane  -t $SESSION:0.3
 
tmux attach -t $SESSION
