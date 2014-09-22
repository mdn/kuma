from .models import FilterGroup
from .serializers import GroupWithFiltersSerializer


def search_filters(request):
    if request.path.startswith('/search'):
        return

    groups = FilterGroup.objects.all()
    serializer = GroupWithFiltersSerializer(groups, many=True)
    return {'command_search_filters': serializer.data}
