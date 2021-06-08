from django.core.exceptions import ValidationError

from kuma.wiki.tests import revision

from . import UserTestCase
from ..models import User, UserBan, UserSubscription


class TestUser(UserTestCase):
    def test_websites(self):
        """A list of websites can be maintained on a user"""
        user = self.user_model.objects.get(username="testuser")

        # Assemble a set of test sites.
        test_sites = {
            "website_url": "http://example.com",
            "twitter_url": "http://twitter.com/lmorchard",
            "github_url": "http://github.com/lmorchard",
            "stackoverflow_url": "http://stackoverflow.com/users/lmorchard",
            "pmo_url": "https://people.mozilla.org/p/testuser",
            "facebook_url": "https://www.facebook.com/test.user",
            "discourse_url": "https://discourse.mozilla.org/u/",
        }

        # Try a mix of assignment cases for the websites property
        for name, url in test_sites.items():
            setattr(user, name, url)

        # Save and make sure a fresh fetch works as expected
        user.save()
        user2 = self.user_model.objects.get(pk=user.pk)
        for name, url in test_sites.items():
            assert url == getattr(user2, name)

    def test_linkedin_urls(self):
        user = self.user_model.objects.get(username="testuser")

        linkedin_urls = [
            "https://in.linkedin.com/in/testuser",
            "https://www.linkedin.com/in/testuser",
            "https://www.linkedin.com/pub/testuser",
        ]

        for url in linkedin_urls:
            user.linkedin_url = url
            user.save()
            new_user = self.user_model.objects.get(pk=user.pk)
            assert url == new_user.linkedin_url

    def test_stackoverflow_urls(self):
        """Bug 1306087: Accept two-letter country-localized stackoverflow
        domains but not meta.stackoverflow.com."""
        user = self.user_model.objects.get(username="testuser")

        valid_stackoverflow_urls = [
            "https://stackoverflow.com/users/testuser",
            "https://es.stackoverflow.com/users/testuser",
        ]

        for valid_url in valid_stackoverflow_urls:
            user.stackoverflow_url = valid_url
            user.full_clean()

        invalid_stackoverflow_urls = [
            "https://1a.stackoverflow.com/users/testuser",
            "https://meta.stackoverflow.com/users/testuser",
        ]

        for invalid_url in invalid_stackoverflow_urls:
            user.stackoverflow_url = invalid_url
            with self.assertRaises(ValidationError):
                user.full_clean()

    def test_irc_nickname(self):
        """We've added IRC nickname as a profile field.
        Make sure it shows up."""
        user = self.user_model.objects.get(username="testuser")
        assert hasattr(user, "irc_nickname")
        assert "testuser" == user.irc_nickname

    def test_locale_timezone_fields(self):
        """We've added locale and timezone fields. Verify defaults."""
        user = self.user_model.objects.get(username="testuser")
        assert hasattr(user, "locale")
        assert user.locale == "en-US"
        assert hasattr(user, "timezone")
        assert "US/Pacific" == user.timezone

    def test_wiki_revisions(self):
        user = self.user_model.objects.get(username="testuser")
        rev = revision(save=True, is_approved=True)
        assert rev.pk in user.wiki_revisions().values_list("pk", flat=True)


class BanTestCase(UserTestCase):
    def test_ban_user(self):
        testuser = self.user_model.objects.get(username="testuser")
        admin = self.user_model.objects.get(username="admin")
        assert testuser.is_active
        ban = UserBan(user=testuser, by=admin, reason="Banned by unit test")
        ban.save()
        testuser_banned = self.user_model.objects.get(username="testuser")
        assert not testuser_banned.is_active
        assert testuser_banned.active_ban.by == admin

        ban.is_active = False
        ban.save()
        testuser_unbanned = self.user_model.objects.get(username="testuser")
        assert testuser_unbanned.is_active

        ban.is_active = True
        ban.save()
        testuser_banned = self.user_model.objects.get(username="testuser")
        assert not testuser_banned.is_active
        assert testuser_unbanned.active_ban

        ban.delete()
        testuser_unbanned = self.user_model.objects.get(username="testuser")
        assert testuser_unbanned.is_active
        assert testuser_unbanned.active_ban is None


def test_user_subscription_set_active(wiki_user):
    UserSubscription.set_active(wiki_user, "abc123")
    assert UserSubscription.objects.filter(user=wiki_user).count() == 1
    assert not UserSubscription.objects.filter(user=wiki_user).first().canceled
    # idempotent
    UserSubscription.set_active(wiki_user, "abc123")
    assert UserSubscription.objects.filter(user=wiki_user).count() == 1
    # different stripe_subscription_id
    UserSubscription.set_active(wiki_user, "xyz789")
    assert UserSubscription.objects.filter(user=wiki_user).count() == 2
    assert (
        UserSubscription.objects.filter(user=wiki_user, canceled__isnull=True).count()
        == 2
    )


def test_user_subscription_set_canceled(wiki_user):
    UserSubscription.set_canceled(wiki_user, "abc123")
    assert UserSubscription.objects.filter(user=wiki_user).count() == 1
    assert UserSubscription.objects.filter(user=wiki_user).first().canceled
    # idempotent
    UserSubscription.set_canceled(wiki_user, "abc123")
    assert UserSubscription.objects.filter(user=wiki_user).count() == 1
    # different stripe_subscription_id
    UserSubscription.set_canceled(wiki_user, "xyz789")
    assert UserSubscription.objects.filter(user=wiki_user).count() == 2
    assert (
        UserSubscription.objects.filter(user=wiki_user, canceled__isnull=False).count()
        == 2
    )


def test_user_subscription_and_subscriber_number(wiki_user):
    """This test checks the relationship between UserSubscription.set_active,
    UserSubscription.set_canceled, and User.subscriber_number."""
    assert wiki_user.subscriber_number is None
    UserSubscription.set_active(wiki_user, "abc123")
    wiki_user.refresh_from_db()
    assert wiki_user.subscriber_number == 1

    # Hit it again, and the subscriber_number shouldn't go up
    UserSubscription.set_active(wiki_user, "abc123")
    wiki_user.refresh_from_db()
    assert wiki_user.subscriber_number == 1

    # And not go down if you cancel
    UserSubscription.set_canceled(wiki_user, "abc123")
    wiki_user.refresh_from_db()
    assert wiki_user.subscriber_number == 1

    # And creating a brand new subscription doesn't change it either
    UserSubscription.set_active(wiki_user, "xyz789")
    wiki_user.refresh_from_db()
    assert wiki_user.subscriber_number == 1


def test_get_highest_subscriber_number(wiki_user):
    assert User.get_highest_subscriber_number() == 0
    UserSubscription.set_active(wiki_user, "abc123")
    assert User.get_highest_subscriber_number() == 1
