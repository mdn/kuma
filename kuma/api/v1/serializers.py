from rest_framework import exceptions
from rest_framework import serializers

from kuma.users.models import User
from kuma.wiki.models import BCSignal, Document


class BCSignalSerializer(serializers.Serializer):
    feature = serializers.CharField(max_length=255)
    browsers = serializers.CharField(max_length=255)
    slug = serializers.CharField(max_length=255)
    locale = serializers.CharField(max_length=7)
    explanation = serializers.CharField(
        # Make sure these match the constants in bcd-signal.jsx
        max_length=1000,
        min_length=10,
    )
    supporting_material = serializers.CharField(
        allow_blank=True, required=False, max_length=1000
    )

    def create(self, validated_data):
        slug = validated_data.pop("slug")
        locale = validated_data.pop("locale")
        document = Document.objects.filter(slug=slug, locale=locale).first()

        if document:
            return BCSignal.objects.create(document=document, **validated_data)
        raise exceptions.ValidationError("Document not found")


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "fullname", "is_newsletter_subscribed", "locale")
