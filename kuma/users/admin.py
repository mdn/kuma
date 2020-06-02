from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from django.utils.html import format_html

from kuma.core.urlresolvers import reverse
from kuma.core.utils import urlparams

from .models import User, UserBan, UserSubscription


@admin.register(UserBan)
class UserBanAdmin(admin.ModelAdmin):
    fields = ("user", "by", "reason", "is_active")
    list_display = ("user", "by", "reason", "is_active")
    list_editable = ("is_active",)
    list_filter = ("is_active",)
    raw_id_fields = ("user", "by")
    search_fields = ("user__username", "reason", "by__username")


class IsStripeCustomer(admin.SimpleListFilter):
    title = "is Stripe customer"
    parameter_name = "is_stripe_customer"

    def lookups(self, request, model_admin):
        return (
            ("yes", "Yes"),
            ("no", "No"),
        )

    def queryset(self, request, queryset):
        value = self.value()
        if value == "yes":
            return queryset.exclude(stripe_customer_id="")
        elif value == "no":
            return queryset.filter(stripe_customer_id="")
        else:
            return queryset


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """
    Extends the admin view of users to show date_joined field
    add a filter on the field too
    """

    fieldsets = BaseUserAdmin.fieldsets + (
        ("Subscription", {"fields": ("stripe_customer_id", "subscriber_number")}),
    )
    readonly_fields = BaseUserAdmin.readonly_fields + (
        "stripe_customer_id",
        "subscriber_number",
    )

    list_display = (
        "username",
        "fullname",
        "email",
        "revisions",
        "date_joined",
        "is_staff",
        "is_active",
    )
    list_filter = (
        "is_staff",
        "is_superuser",
        "is_active",
        "date_joined",
        "groups",
        IsStripeCustomer,
    )
    ordering = ("-date_joined",)
    search_fields = (
        "username",
        "title",
        "fullname",
        "organization",
        "location",
        "email",
    )

    def revisions(self, obj):
        """HTML link to user's revisions with count"""
        link = urlparams(reverse("dashboards.revisions"), user=obj.username)
        count = obj.created_revisions.count()
        return format_html('<a href="{}"><strong>{}</strong></a>', link, count)


@admin.register(UserSubscription)
class UserSubscriptionAdmin(admin.ModelAdmin):
    readonly_fields = ("user", "updated", "created", "stripe_subscription_id")
    list_display = ("user", "canceled", "updated", "created")
    search_fields = ("user__username",)
    list_filter = ("canceled", "created")
    ordering = ("updated",)
