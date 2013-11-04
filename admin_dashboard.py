"""
This file was generated with the customdashboard management command and
contains the class for the main dashboard.

To activate your index dashboard add the following to your settings.py::
    GRAPPELLI_INDEX_DASHBOARD = 'admin_dashboard.CustomIndexDashboard'
"""

from django.utils.translation import ugettext_lazy as _
from grappelli.dashboard import modules, Dashboard


class CustomIndexDashboard(Dashboard):
    """
    Custom index dashboard for www.
    """
    def init_with_context(self, context):

        self.children.append(modules.ModelList(
            title='Wiki',
            column=1,
            models=(
                'wiki.models.Document',
                'wiki.models.DocumentZone',
                'wiki.models.DocumentTag',
                'wiki.models.Revision',
                'wiki.models.Attachment',
                'wiki.models.AttachmentRevision',
                'wiki.models.EditorToolbar',
            )
        ))

        self.children.append(modules.ModelList(
            title='Demo Studio',
            column=1,
            models=(
                'demos.models.*',
            )
        ))

        self.children.append(modules.AppList(
            title='Access Control',
            column=2,
            collapsible=True,
            models=(
                'django.contrib.auth.*',
                'teamwork.*',
                'users.*',
            ),
        ))

        self.children.append(modules.AppList(
            title='Site Operations',
            column=2,
            collapsible=True,
            models=(
                'waffle.*',
                'constance.*',
                'soapbox.*',
                'django.contrib.sites.*',
            ),
        ))

        self.children.append(modules.AppList(
            title=_('Other Applications'),
            column=1,
            collapsible=True,
            exclude=(
                'wiki.*',
                'demos.*',
                'users.*',
                'waffle.*',
                'constance.*',
                'soapbox.*',
                'teamwork.*',
                'django.contrib.auth.*',
                'django.contrib.sites.*',
            ),
        ))

        self.children.append(modules.RecentActions(
            _('Your Recent Actions'),
            limit=5,
            collapsible=False,
            column=3,
        ))
