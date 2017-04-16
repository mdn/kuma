#!/usr/bin/env python
from werkzeug import script

def make_app():
    from shorty.application import Shorty
    return Shorty('sqlite:////tmp/shorty.db')

def make_shell():
    from shorty import models, utils
    application = make_app()
    return locals()

action_runserver = script.make_runserver(make_app, use_reloader=True)
action_shell = script.make_shell(make_shell)
action_initdb = lambda: make_app().init_database()

script.run()
