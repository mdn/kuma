from django.contrib import admin

from .models import LandingPageSurvey


class HasEmailFilter(admin.SimpleListFilter):
    title = "Has email"
    parameter_name = "has_email"

    def lookups(self, request, model_admin):
        return (
            ("true", "Has email"),
            ("false", "No email"),
        )

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.exclude(email="")
        if self.value() == "false":
            return queryset.filter(email="")


class HasResponseFilter(admin.SimpleListFilter):
    title = "Has response"
    parameter_name = "has_response"

    def lookups(self, request, model_admin):
        return (
            ("true", "Has response"),
            ("false", "No response"),
        )

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(response__isnull=False)
        if self.value() == "false":
            return queryset.filter(response__isnull=True)


@admin.register(LandingPageSurvey)
class LandingPageSurveyAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "variant",
        "geo_information",
        "has_email",
        "has_response",
        "created",
    )
    fields = (
        "variant",
        "geo_information",
        "response",
        "email",
    )
    readonly_fields = ("geo_information", "response", "variant", "email")

    list_filter = (
        HasEmailFilter,
        HasResponseFilter,
    )
    search_fields = ("email",)
    ordering = ("created",)

    def has_email(self, obj):
        return bool(obj.email)

    def has_response(self, obj):
        return bool(obj.response)
