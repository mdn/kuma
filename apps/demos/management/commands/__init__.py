# HACK: monkey-patch natural key onto User for django 1.2
# see https://code.djangoproject.com/ticket/13914#comment:26
from django.contrib.auth import models as auth_models


def user_natural_key(self):
    return (self.username,)


class UserManagerWithNaturalKey(auth_models.UserManager):
    def get_by_natural_key(self, username):
        try:
            return self.get(username=username)
        except auth_models.User.DoesNotExist:
            return None


    def contribute_to_class(self, model, name):
        super(UserManagerWithNaturalKey, self).contribute_to_class(model, name)


umwnk = UserManagerWithNaturalKey()
auth_models.User._default_manager = umwnk
auth_models.User.objects = umwnk
umwnk.contribute_to_class(auth_models.User, '_default_manager')
umwnk.contribute_to_class(auth_models.User, 'objects')
auth_models.User.natural_key = user_natural_key
