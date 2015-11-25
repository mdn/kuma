from kuma.core.jobs import KumaJob


class AvailableFiltersJob(KumaJob):
    """
    Cache the available search filters.
    """
    lifetime = 60 * 60 * 24

    def fetch(self, *args, **kwargs):
        from .models import Filter

        return (Filter.objects.filter(enabled=True)
                              .prefetch_related('tags', 'group'))
