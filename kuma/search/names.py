"""
Names of filters and filter groups in the search interface.

This is generated from the production database using the management command:

./manage.py generate_search_names.py
"""
from django.utils.translation import gettext_lazy as _

FILTER_NAMES = {
    _("Document type"): [_("Code Samples"), _("How-To & Tutorial"), _("Tools")],
    _("Skill level"): [_("I'm Learning"), _("I'm an Expert"), _("I'm an Intermediate")],
    _("Topics"): [
        _("APIs and DOM"),
        _("Add-ons & Extensions"),
        _("CSS"),
        _("Canvas"),
        _("Firefox"),
        _("Firefox OS"),
        _("Firefox for Android"),
        _("Firefox for Desktop"),
        _("Games"),
        _("HTML"),
        _("HTTP"),
        _("JavaScript"),
        _("Marketplace"),
        _("MathML"),
        _("Mobile"),
        _("Open Web Apps"),
        _("SVG"),
        _("Web Development"),
        _("WebExtensions"),
        _("WebGL"),
        _("Writing Documentation"),
        _("XPCOM"),
        _("XUL"),
    ],
}
