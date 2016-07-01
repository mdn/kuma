from django.contrib.auth import get_user_model
from django.utils.crypto import get_random_string
from allauth.account.models import EmailAddress

from kuma.core.tests import KumaTestCase, KumaTransactionTestCase
from kuma.wiki.tests import revision as create_revision, document as create_document


class UserTestMixin(object):
    """Base TestCase for the users app test cases."""
    fixtures = ['test_users.json']

    def setUp(self):
        super(UserTestMixin, self).setUp()
        self.user_model = get_user_model()


class UserTestCase(UserTestMixin, KumaTestCase):
    pass


class UserTransactionTestCase(UserTestMixin, KumaTransactionTestCase):
    pass


def user(save=False, **kwargs):
    if 'username' not in kwargs:
        kwargs['username'] = get_random_string(length=15)
    password = kwargs.pop('password', 'password')
    groups = kwargs.pop('groups', [])
    user = get_user_model()(**kwargs)
    user.set_password(password)
    if save:
        user.save()
    if groups:
        user.groups = groups
    return user


def email(save=False, **kwargs):
    if 'user' not in kwargs:
        kwargs['user'] = user(save=True)
    if 'email' not in kwargs:
        kwargs['email'] = '%s@%s.com' % (get_random_string(),
                                         get_random_string())
    email = EmailAddress(**kwargs)
    if save:
        email.save()
    return email


class SampleRevisionsMixin(object):
    """Mixin with an original revision and a method to create more revisions."""
    def setUp(self):
        super(SampleRevisionsMixin, self).setUp()

        # Some users to use in the tests
        self.testuser = self.user_model.objects.get(username='testuser')
        self.testuser2 = self.user_model.objects.get(username='testuser2')
        self.admin = self.user_model.objects.get(username='admin')

        # Create an original revision on a document by the admin user
        self.document = create_document(save=True)
        self.original_revision = create_revision(
            title='Revision 0',
            document=self.document,
            creator=self.admin,
            save=True)

    def create_revisions(self, num, creator, document=None):
        """Create as many revisions as requested, and return a list of them."""
        # If document is None, then we create a new document for each revision
        create_new_documents = False
        if not document:
            create_new_documents = True
        revisions_created = []
        for i in range(1, 1 + num):
            if create_new_documents is True:
                document = create_document(save=True)
            new_revision = create_revision(
                title='Revision {}'.format(i),
                document=document,
                creator=creator,
                save=True)
            revisions_created.append(new_revision)
        return revisions_created
