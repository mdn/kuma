# import time
# from dataclasses import dataclass
# from datetime import datetime
# from unittest.mock import patch

# import pytest
# from django.conf import settings
# from django.test import Client
# from django.urls import reverse
# from waffle.testutils import override_flag

# from kuma.core.utils import safer_pyquery as pq
# from kuma.users.models import User, UserSubscription


# @dataclass
# class StripeCustomerSource:
#     object: str
#     brand: str
#     exp_month: int
#     exp_year: int
#     last4: int

#     def get(self, key, default=None):
#         return getattr(self, key, default)


# @dataclass
# class StripeCustomer:
#     email: str
#     default_source: StripeCustomerSource


# @dataclass
# class StripeSubscriptionPlan:
#     amount: int


# @dataclass
# class StripeSubscription:
#     id: str
#     current_period_end: int
#     plan: StripeSubscriptionPlan


# def mock_get_stripe_customer(user):
#     return StripeCustomer(
#         email=user.email,
#         default_source=StripeCustomerSource(
#             object="card",
#             brand="MagicCard",
#             exp_month=12,
#             exp_year=2020,
#             last4=4242,
#         ),
#     )


# def mock_get_stripe_subscription_info(customer, id="sub_123456789"):
#     return StripeSubscription(
#         id=id,
#         current_period_end=time.time() + 10_000,
#         plan=StripeSubscriptionPlan(amount=int(settings.CONTRIBUTION_AMOUNT_USD * 100)),
#     )


# @pytest.fixture
# def test_user(db, django_user_model):
#     return User.objects.create(
#         username="test_user",
#         email="staff@example.com",
#         date_joined=datetime(2019, 1, 17, 15, 42),
#     )


# @patch("kuma.users.views.create_stripe_customer_and_subscription_for_user")
# @patch("kuma.users.stripe_utils.get_stripe_customer")
# @override_flag("subscription", True)
# def test_create_stripe_subscription(mock1, mock2, test_user):
#     customer = mock_get_stripe_customer(test_user)
#     mock1.return_value = customer
#     mock2.return_value = mock_get_stripe_subscription_info(customer)
#     client = Client()
#     client.force_login(test_user)

#     response = client.post(
#         reverse("users.create_stripe_subscription"),
#         data={"stripe_token": "tok_visa", "stripe_email": "payer@example.com"},
#         HTTP_HOST=settings.WIKI_HOST,
#     )
#     assert response.status_code == 302
#     edit_profile_url = reverse("users.user_edit", args=[test_user.username])
#     assert edit_profile_url in response["location"]
#     assert response["location"].endswith("#subscription")


# @override_flag("subscription", True)
# @override_flag("subscription_form", True)
# def test_next_subscriber_number_shown_for_non_subscribers(test_user):
#     client = Client()
#     client.force_login(test_user)
#     response = client.get(reverse("users.user_edit", args=[test_user.username]))
#     assert response.status_code == 200
#     page = pq(response.content)
#     assert "You will be MDN member number 1" in page("#subscription p").text()


# @patch("kuma.users.stripe_utils.get_stripe_subscription_info")
# @patch("kuma.users.stripe_utils.get_stripe_customer")
# @override_flag("subscription", True)
# @pytest.mark.django_db
# def test_user_edit_with_subscription_info(mock1, mock2, test_user):
#     """The user has already signed up for a subscription and now the user edit
#     page contains information about that from Stripe."""
#     mock1.side_effect = mock_get_stripe_customer
#     mock2.side_effect = mock_get_stripe_subscription_info

#     # We need to fake the User.subscriber_number because the
#     # 'get_stripe_subscription_info' is faked so the signals that set it are
#     # never happening in this context.
#     UserSubscription.set_active(test_user, "sub_123456789")
#     # sanity check
#     test_user.refresh_from_db()
#     assert test_user.subscriber_number == 1

#     client = Client()
#     client.force_login(test_user)
#     response = client.post(
#         reverse("users.user_edit", args=[test_user.username]),
#         HTTP_HOST=settings.WIKI_HOST,
#     )
#     assert response.status_code == 200
#     page = pq(response.content)
#     assert page("#subscription h2").text() == "You are MDN member number 1"
#     assert not page(".stripe-error").size()
#     assert "MagicCard ending in 4242" in page(".card-info p").text()


# @patch("kuma.users.stripe_utils.create_stripe_customer_and_subscription_for_user")
# @patch(
#     "kuma.users.stripe_utils.get_stripe_subscription_info",
#     side_effect=mock_get_stripe_subscription_info,
# )
# @override_flag("subscription", False)
# def test_create_stripe_subscription_fail(mock1, mock2, test_user):
#     client = Client()
#     client.force_login(test_user)
#     response = client.post(
#         reverse("users.create_stripe_subscription"),
#         data={"stripe_token": "tok_visa", "stripe_email": "payer@example.com"},
#         follow=True,
#         HTTP_HOST=settings.WIKI_HOST,
#     )
#     assert response.status_code == 403
