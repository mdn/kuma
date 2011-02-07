from celery.decorators import task

from notifications.models import Watch


@task(rate_limit='1/m')
def claim_watches(user):
    """Look for anonymous watches with this user's email and attach them to the
    user."""
    Watch.objects.filter(email=user.email).update(email=None, user=user)
