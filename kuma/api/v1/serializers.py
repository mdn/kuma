from rest_framework import exceptions
from rest_framework import serializers

from kuma.wiki.models import BCSignal, Document


class BCSignalSerializer(serializers.Serializer):
    slug = serializers.CharField()
    locale = serializers.CharField()

    def create(self, validated_data):
        document = Document.objects.filter(
            slug=validated_data['slug'],
            locale=validated_data['locale']
        ).first()

        if document:
            return BCSignal.objects.create(document=document)
        raise exceptions.ValidationError('Document not found')
