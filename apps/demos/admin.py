from django.contrib import admin

from .models import Submission


class SubmissionAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'
    
    list_display = ( 'title', 'creator', 'featured', 'hidden', 'censored', 'tags', 'modified', )
    def queryset(self, request):
        return Submission.admin_manager

admin.site.register(Submission, SubmissionAdmin)

