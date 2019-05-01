import django.dispatch

render_done = django.dispatch.Signal(providing_args=["instance"])
