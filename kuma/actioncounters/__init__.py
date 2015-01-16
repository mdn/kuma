"""
This is a Django app intended to help count actions on model content objects.
Examples of actions include things such as "view", "download", and "like".
An attempt is made to constrain each counted action to a limit per unique user.

Inspired in part by:
* <https://github.com/thornomad/django-hitcount>
* <https://github.com/dcramer/django-ratings>
"""
