from django.core.exceptions import ValidationError

from . import BannerTestCase
from ..models import Banner


class TestBanner(BannerTestCase):

    def test_add_new_banner(self):
        """Test that banner creation succeeds"""
        sample_banner = {
            "banner_name": "GreatSuccess",
            "banner_title": "Active Banner",
            "banner_copy": "Some sample main copy",
            "banner_button_copy": "Click Me!",
            "banner_theme": "default",
            "banner_active": "True",
            "banner_priority": "2"
        }
        banner = Banner.objects.create(**sample_banner)

        self.assertTrue(isinstance(banner, Banner))
        self.assertEqual(banner.banner_name, "GreatSuccess")

    def test_default_theme_set(self):
        """Test that theme is set to default if empty"""
        banner = Banner.objects.get(banner_name="notheme")

        self.assertTrue(isinstance(banner, Banner))
        self.assertEqual(banner.banner_theme, "default")

    def test_default_priority_set(self):
        """Test that priority is set to 100 if empty"""
        banner = Banner.objects.get(banner_name="nopriority")

        self.assertTrue(isinstance(banner, Banner))
        self.assertEqual(banner.banner_priority, 100)

    def test_activate_banner(self):
        """Test changing banner state from inactive to active"""
        banner = Banner.objects.get(banner_name="inactive")
        self.assertEqual(banner.banner_active, False)
        banner.banner_active = True
        banner.save()

        banner2 = Banner.objects.get(pk=banner.pk)
        self.assertEqual(banner2.banner_active, True)

    def test_fails_when_max_length_exceeded(self):
        """Test raises error when field max_length exceeded"""

        sample_banner = {
            "banner_name": "This Name Should Cause A ValidationError To Be Raised",
            "banner_title": "Active Banner",
            "banner_copy": "Some sample main copy",
            "banner_button_copy": "Click Me!",
            "banner_theme": "default",
            "banner_active": "True",
            "banner_priority": "2"
        }
        with self.assertRaises(ValidationError):
            banner = Banner(**sample_banner)
            banner.full_clean()
