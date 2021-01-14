from rest_framework import serializers

from kuma.users.models import User


class UserDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "fullname", "is_newsletter_subscribed", "locale")
