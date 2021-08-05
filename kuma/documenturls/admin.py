from django.contrib import admin

from .models import DocumentURL, DocumentURLCheck


@admin.register(DocumentURL)
class DocumentURLAdmin(admin.ModelAdmin):
    list_display = (
        "uri",
        "absolute_url",
        "is_valid",
        "modified",
    )
    readonly_fields = (
        "metadata",
        "invalid",
        "created",
        "modified",
    )

    list_filter = ("invalid",)
    search_fields = ("uri",)
    ordering = ("-created",)
    list_per_page = 10

    def is_valid(self, obj):
        return not obj.invalid


@admin.register(DocumentURLCheck)
class DocumentURLCheckAdmin(admin.ModelAdmin):
    list_display = (
        "_documenturl",
        "http_error",
        "created",
    )
    readonly_fields = (
        "document_url",
        "http_error",
        "headers",
        "created",
    )

    list_filter = ("http_error",)
    search_fields = ("documenturl__uri", "document_url__absolute_url")
    ordering = ("-created",)
    list_per_page = 10

    def _documenturl(self, obj):
        return obj.document_url.absolute_url
