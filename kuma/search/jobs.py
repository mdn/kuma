from kuma.core.jobs import KumaJob


class AvailableFiltersJob(KumaJob):

    def fetch(self, *args, **kwargs):
        from .models import Filter

        return (Filter.objects.filter(enabled=True)
                              .prefetch_related('tags', 'group'))
