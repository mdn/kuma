from kuma.core.jobs import KumaJob
from .utils import spam_dashboard_recent_events


class SpamDashboardRecentEvents(KumaJob):
    """Cache recent event data for a very short time."""
    lifetime = 60
    fetch_on_miss = True
    version = 2

    def fetch(self):
        return spam_dashboard_recent_events()
