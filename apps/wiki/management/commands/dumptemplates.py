from django.core.management.base import BaseCommand
from django.core.management.commands.dumpdata import sort_dependencies
from django.core import serializers

import wiki.models
from wiki.models import Document, Revision

class Command(BaseCommand):
    def handle(self, **options):
        objects = []
        for model in sort_dependencies([(wiki.models, [Document, Revision])]):
            if model.__name__ == 'Document':
                objects.extend(model._default_manager.filter(
                                                    slug__startswith='Template:'))
            elif model.__name__ == 'Revision':
                objects.extend(model._default_manager.filter(
                                        document__slug__startswith='Template:'))
            else:
                objects.extend(model._default_manager.all())

        serializers.get_serializer('json')
        return serializers.serialize('json', objects, indent=4)
