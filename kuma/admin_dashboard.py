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
                'kuma.wiki.models.Document',
                'kuma.wiki.models.DocumentZone',
                'kuma.wiki.models.DocumentTag',
                'kuma.wiki.models.Revision',
                'kuma.wiki.models.Attachment',
                'kuma.wiki.models.AttachmentRevision',
                'kuma.wiki.models.EditorToolbar',
            )
        ))

        self.children.append(modules.ModelList(
            title='Demo Studio',
            column=1,
            models=(
                'kuma.demos.models.*',
            )
        ))

        self.children.append(modules.AppList(
            title='Access Control',
            column=2,
            collapsible=True,
            models=(
                'django.contrib.auth.*',
                'kuma.users.*',
                'allauth.account.*',
                'allauth.socialaccount.*',
                'teamwork.*',
                'kuma.authkeys.*',
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
                'kuma.search.*',
                'djcelery.*',
            ),
        ))

        self.children.append(modules.AppList(
            title=_('Other Applications'),
            column=1,
            collapsible=True,
            exclude=(
                'kuma.wiki.*',
                'kuma.demos.*',
                'kuma.users.*',
                'waffle.*',
                'constance.*',
                'soapbox.*',
                'teamwork.*',
                'django.contrib.auth.*',
                'django.contrib.sites.*',
                'allauth.account.*',
                'allauth.socialaccount.*',
                'djcelery.*',
                'kuma.authkeys.*',
            ),
        ))

        self.children.append(modules.RecentActions(
            _('Your Recent Actions'),
            limit=5,
            collapsible=False,
            column=3,
        ))
