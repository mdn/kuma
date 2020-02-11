import django.dispatch

render_done = django.dispatch.Signal(
    providing_args=["instance", "invalidate_cdn_cache"]
)
restore_done = django.dispatch.Signal(providing_args=["instance"])
