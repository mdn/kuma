SESSION=$USER

tmux has-session -t $SESSION
if [ $? -eq 0 ]; then
    echo "Session $SESSION already exists. Attaching."
    sleep 1
    tmux attach -t $SESSION
    exit 0;
fi

tmux new-session -d -s $SESSION

tmux split-window -t $SESSION:0 -v -p 50 './manage.py runserver 0.0.0.0:8000; /bin/bash'
tmux swap-pane    -t $SESSION:0 -U
tmux split-window -t $SESSION:0 -v -p 50 'node kumascript/run.js; /bin/bash'
tmux select-pane  -t $SESSION:0.2
 
tmux attach -t $SESSION
