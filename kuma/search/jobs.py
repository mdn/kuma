from kuma.core.jobs import KumaJob


class AvailableFiltersJob(KumaJob):
    lifetime = 60 * 60 * 24
    refresh_timeout = 15

    def fetch(self, *args, **kwargs):
        from .models import Filter

        return (Filter.objects.filter(enabled=True)
                              .prefetch_related('tags', 'group'))


class CommandFiltersJob(KumaJob):
    lifetime = 60 * 60 * 24
    refresh_timeout = 15

    def fetch(self, *args, **kwargs):
        from .models import FilterGroup
        from .serializers import GroupWithFiltersSerializer

        groups = FilterGroup.objects.all()
        serializer = GroupWithFiltersSerializer(groups, many=True)
        return {'command_search_filters': serializer.data}
