SESSION=$USER

tmux has-session -t $SESSION
if [ $? -eq 0 ]; then
    echo "Session $SESSION already exists. Attaching."
    sleep 1
    tmux attach -t $SESSION
    exit 0;
fi

tmux new-session -d -s $SESSION

tmux split-window -t $SESSION:0 -v -p 50 
tmux send-keys -t $SESSION:0 './manage.py celeryd --events --beat --autoreload' Enter
tmux swap-pane    -t $SESSION:0 -U
tmux split-window -t $SESSION:0 -v -p 50
tmux send-keys -t $SESSION:0 './manage.py runserver 0.0.0.0:8000' Enter
tmux swap-pane    -t $SESSION:0 -U
tmux split-window -t $SESSION:0 -v -p 50
tmux send-keys -t $SESSION:0 'node kumascript/run.js' Enter
tmux select-pane  -t $SESSION:0.3
 
tmux attach -t $SESSION
