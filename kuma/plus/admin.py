from django.contrib import admin

from .models import LandingPageSurvey


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
        "geo_information",
        "has_response",
        "created",
    )
    fields = (
        "geo_information",
        "response",
    )
    readonly_fields = (
        "geo_information",
        "response",
    )

    list_filter = (HasResponseFilter,)
    search_fields = ("response", "uuid", "geo_information")
    ordering = ("-created",)
    list_per_page = 10

    def has_email(self, obj):
        return bool(obj.email)

    def has_response(self, obj):
        return bool(obj.response)

    def signed_in(self, obj):
        return bool(obj.user)
