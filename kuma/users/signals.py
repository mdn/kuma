import django.dispatch

newsletter_subscribed = django.dispatch.Signal(providing_args=["user"])
newsletter_unsubscribed = django.dispatch.Signal(providing_args=["user"])

username_changed = django.dispatch.Signal(providing_args=["user"])
