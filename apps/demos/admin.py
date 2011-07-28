from django.contrib import admin

from .models import Submission

from taggit_extras.managers import NamespacedTaggableManager
from taggit.forms import TagWidget, TagField


class SubmissionAdmin(admin.ModelAdmin):
    change_list_template = 'smuggler/change_list.html'
    
    list_display = ('title', 'creator', 'featured', 'censored', 'taggit_tags',
                    'modified', )

    list_editable = ('featured', 'censored', 'taggit_tags', )

    search_fields = ('title', 'summary', 'description', 'taggit_tags__name')

    list_filter = ('created', 'modified') #, 'taggit_tags' )

    formfield_overrides = {
        NamespacedTaggableManager: {
            "widget": TagWidget(attrs={"size": 70})
        }
    }

    def queryset(self, request):
        return Submission.admin_manager

admin.site.register(Submission, SubmissionAdmin)
