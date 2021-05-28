from django.conf import settings
from django.utils.translation import gettext
from rest_framework import serializers

from . import models
from .fields import SiteURLField


class SearchQuerySerializer(serializers.Serializer):
    q = serializers.CharField(required=False, max_length=settings.ES_Q_MAXLENGTH)
    highlight = serializers.BooleanField(required=False, default=True)
    # Advanced search query paramenters.
    css_classnames = serializers.CharField(required=False)
    html_attributes = serializers.CharField(required=False)

    def validate_q(self, value):
        # Check that \n not in query
        if r"\n" in value:
            raise serializers.ValidationError("Search term must not contain new line")
        return value


class FilterURLSerializer(serializers.Serializer):
    active = serializers.ReadOnlyField()
    inactive = serializers.ReadOnlyField()


class FacetedFilterOptionsSerializer(serializers.Serializer):
    name = serializers.ReadOnlyField()
    slug = serializers.ReadOnlyField()
    count = serializers.ReadOnlyField()
    active = serializers.BooleanField(read_only=True, default=False)
    urls = FilterURLSerializer(read_only=True)


class FacetedFilterSerializer(serializers.Serializer):
    name = serializers.ReadOnlyField()
    slug = serializers.ReadOnlyField()
    options = FacetedFilterOptionsSerializer(many=True)


class BaseDocumentSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(read_only=True, max_length=255)
    slug = serializers.CharField(read_only=True, max_length=255)
    locale = serializers.CharField(read_only=True, max_length=7)
    url = SiteURLField("wiki.document", args=["slug"])
    edit_url = SiteURLField("wiki.edit", args=["slug"])

    def get_attribute(self, obj):
        # Pass the entire object through to `to_representation()`,
        # instead of the standard attribute lookup.
        return obj

    def to_representation(self, value):
        if self.field_name == "parent" and not getattr(value, "parent", None):
            return {}
        return super(BaseDocumentSerializer, self).to_representation(value)


class DocumentSerializer(BaseDocumentSerializer):
    excerpt = serializers.ReadOnlyField(source="get_excerpt")
    tags = serializers.ListField(read_only=True)
    score = serializers.FloatField(
        read_only=True,
        source="meta.score",
        allow_null=True,
    )
    parent = BaseDocumentSerializer(read_only=True, allow_null=True)


class FilterSerializer(serializers.ModelSerializer):
    name = serializers.SerializerMethodField("get_localized_name")
    slug = serializers.ReadOnlyField(required=False)
    shortcut = serializers.ReadOnlyField(required=False)

    class Meta:
        model = models.Filter
        depth = 1
        fields = ("name", "slug", "shortcut")

    def get_localized_name(self, obj):
        return gettext(obj.name)


class GroupSerializer(serializers.Serializer):
    name = serializers.ReadOnlyField()
    slug = serializers.ReadOnlyField()
    order = serializers.ReadOnlyField()


class FilterWithGroupSerializer(FilterSerializer):
    tags = serializers.SerializerMethodField("get_tag_names")
    group = GroupSerializer(read_only=True)

    def get_tag_names(self, obj):
        return obj.tags.names()

    class Meta(FilterSerializer.Meta):
        fields = FilterSerializer.Meta.fields + ("tags", "operator", "group")
