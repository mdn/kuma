from celery import task

from kuma.core.decorators import skip_in_maintenance_mode

from .utils import update_feeds as utils_update_feeds


@task
@skip_in_maintenance_mode
def update_feeds():
    """Update republished feeds like the Hacks Blog."""
    utils_update_feeds()
