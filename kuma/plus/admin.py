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


class SignedInFilter(admin.SimpleListFilter):
    title = "Signed in"
    parameter_name = "signed_in"

    def lookups(self, request, model_admin):
        return (
            ("true", "Signed in"),
            ("false", "Anonymous"),
        )

    def queryset(self, request, queryset):
        if self.value() == "true":
            return queryset.filter(user__isnull=False)
        if self.value() == "false":
            return queryset.filter(user__isnull=True)


@admin.register(LandingPageSurvey)
class LandingPageSurveyAdmin(admin.ModelAdmin):
    list_display = (
        "uuid",
        "variant",
        "geo_information",
        "has_email",
        "has_response",
        "signed_in",
        "created",
    )
    fields = (
        "variant",
        "geo_information",
        "response",
        "email",
        "user",
    )
    readonly_fields = ("geo_information", "response", "variant", "email", "user")

    list_filter = (HasEmailFilter, HasResponseFilter, SignedInFilter, "variant")
    search_fields = ("email", "uuid")
    ordering = ("-created",)
    list_per_page = 10

    def has_email(self, obj):
        return bool(obj.email)

    def has_response(self, obj):
        return bool(obj.response)

    def signed_in(self, obj):
        return bool(obj.user)
