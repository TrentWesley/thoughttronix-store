"""The Security Center hub: access, own-account data, and the email reminder."""

from http import HTTPStatus

import pytest
from django.urls import reverse

REMINDER = "Add an email address to protect your account"


def test_hub_lives_at_accounts_security():
    assert reverse("accounts:security") == "/accounts/security/"


def test_signed_out_visitor_is_sent_to_sign_in_with_next(client, db):
    response = client.get(reverse("accounts:security"))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('accounts:login')}?next=/accounts/security/"


def test_signing_in_through_next_returns_to_the_hub(client, customer):
    response = client.post(
        reverse("accounts:login"),
        {
            "username": "customer",
            "password": "customer123",
            "next": reverse("accounts:security"),
        },
        follow=True,
    )

    assert response.redirect_chain[-1][0] == reverse("accounts:security")
    assert response.context["user"] == customer


@pytest.mark.parametrize("who", ["customer", "staff_user", "superuser"])
def test_every_signed_in_role_sees_their_own_hub(client, request, who):
    user = request.getfixturevalue(who)
    client.force_login(user)

    response = client.get(reverse("accounts:security"))

    assert response.status_code == HTTPStatus.OK
    assert response.context["user"] == user
    assert user.username in response.content.decode()


def test_user_with_email_sees_address_and_no_reminder(client, customer_with_email):
    client.force_login(customer_with_email)

    page = client.get(reverse("accounts:security")).content.decode()

    assert "casey@example.com" in page
    assert REMINDER not in page


def test_user_without_email_sees_reminder(client, customer):
    client.force_login(customer)

    page = client.get(reverse("accounts:security")).content.decode()

    assert REMINDER in page


def test_query_input_cannot_select_another_user(client, customer, customer_with_email):
    client.force_login(customer)

    response = client.get(
        reverse("accounts:security"),
        {"user": customer_with_email.pk, "username": "casey"},
    )

    page = response.content.decode()
    assert response.context["user"] == customer
    assert "casey@example.com" not in page
    assert REMINDER in page


def test_user_without_email_can_still_shop(client, customer, product):
    client.force_login(customer)

    assert client.get(reverse("products:catalog")).status_code == HTTPStatus.OK
    assert client.get(product.get_absolute_url()).status_code == HTTPStatus.OK
    client.post(reverse("orders:add", kwargs={"pk": product.pk}))
    assert client.get(reverse("orders:cart")).status_code == HTTPStatus.OK
    assert customer.cart.item_count() == 1
