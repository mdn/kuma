from kuma.core.jobs import KumaJob
from .utils import spam_day_stats, spam_dashboard_recent_events


class SpamDayStats(KumaJob):
    """Cache spam stats for multiple days."""
    lifetime = 60 * 60 * 24 * 7
    fetch_on_miss = True
    version = 8

    def fetch(self, day):
        return spam_day_stats(day)


class SpamDashboardRecentEvents(KumaJob):
    """Cache recent event data for a very short time."""
    lifetime = 60
    fetch_on_miss = True
    version = 2

    def fetch(self):
        return spam_dashboard_recent_events()
