from django.contrib import admin

from .models import Submission


class SubmissionAdmin(admin.ModelAdmin):
    list_display = ( 'title', 'creator', 'featured', 'hidden', 'tags', 'modified', )
    list_editable = ( 'featured', 'hidden' )

admin.site.register(Submission, SubmissionAdmin)

