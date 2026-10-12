"""Updating the recovery email from the Security Center, and its masked notice."""

from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.core import mail
from django.urls import reverse

from accounts.models import mask_email

ALREADY_YOURS = "That&#x27;s already your email address."
SUCCESS = "Your email address has been updated."


def change(client, password, email):
    return client.post(
        reverse("accounts:email_change"),
        {"current_password": password, "email": email},
    )


def test_email_change_lives_under_security():
    assert reverse("accounts:email_change") == "/accounts/security/email/"


def test_signed_out_visitor_is_sent_to_sign_in_with_next(client, db):
    response = client.get(reverse("accounts:email_change"))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == f"{reverse('accounts:login')}?next=/accounts/security/email/"


def test_hub_links_to_email_change(client, customer_with_email):
    client.force_login(customer_with_email)

    page = client.get(reverse("accounts:security")).content.decode()

    assert reverse("accounts:email_change") in page


def test_reminder_links_to_email_change(client, customer):
    client.force_login(customer)

    page = client.get(reverse("accounts:security")).content.decode()

    reminder = page[page.index("Add an email address to protect your account") :]
    assert reverse("accounts:email_change") in reminder[: reminder.index("</div>")]


def test_wrong_password_is_rejected(client, customer_with_email):
    client.force_login(customer_with_email)

    response = change(client, "not-my-password", "new@example.com")

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["current_password"]
    customer_with_email.refresh_from_db()
    assert customer_with_email.email == "casey@example.com"
    assert mail.outbox == []


@pytest.mark.parametrize(
    "typed", ["taken@example.com", "TAKEN@Example.com", "  Taken@EXAMPLE.COM  "]
)
def test_address_of_another_account_is_rejected(client, customer_with_email, typed):
    get_user_model().objects.create_user(username="other", email="taken@example.com")
    client.force_login(customer_with_email)

    response = change(client, "casey12345", typed)

    assert response.status_code == HTTPStatus.OK
    assert "already belongs to another account" in response.content.decode()
    customer_with_email.refresh_from_db()
    assert customer_with_email.email == "casey@example.com"
    assert mail.outbox == []


@pytest.mark.parametrize(
    "typed", ["casey@example.com", "CASEY@EXAMPLE.COM", " Casey@Example.com "]
)
def test_own_current_address_is_rejected(client, customer_with_email, typed):
    client.force_login(customer_with_email)

    response = change(client, "casey12345", typed)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"] == [
        "That's already your email address."
    ]
    assert ALREADY_YOURS in response.content.decode()
    customer_with_email.refresh_from_db()
    assert customer_with_email.email == "casey@example.com"
    assert mail.outbox == []


def test_invalid_address_is_rejected(client, customer_with_email):
    client.force_login(customer_with_email)

    response = change(client, "casey12345", "not-an-email")

    assert response.context["form"].errors["email"]
    customer_with_email.refresh_from_db()
    assert customer_with_email.email == "casey@example.com"
    assert mail.outbox == []


def test_valid_change_saves_normalized_address_and_returns_to_hub(
    client, customer_with_email
):
    client.force_login(customer_with_email)

    response = change(client, "casey12345", "  Sam@Example.COM  ")

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:security")
    customer_with_email.refresh_from_db()
    assert customer_with_email.email == "Sam@example.com"
    hub = client.get(response.url).content.decode()
    assert SUCCESS in hub
    assert "Sam@example.com" in hub


def test_valid_change_sends_one_masked_notice_to_the_old_address(
    client, settings, customer_with_email
):
    settings.SUPPORT_EMAIL = "help-desk@thoughttronix.example"
    client.force_login(customer_with_email)

    change(client, "casey12345", "sam@example.com")

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.to == ["casey@example.com"]
    assert message.cc == []
    assert message.bcc == []
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    body = message.body
    assert "casey" in body
    assert "UTC" in body
    assert "s***@example.com" in body
    assert "help-desk@thoughttronix.example" in body
    assert "sam@example.com" not in body
    assert "reset" not in body.lower()
    assert "Forgot your password" not in body
    assert "casey12345" not in body


def test_adding_a_first_email_saves_and_sends_nothing(client, customer):
    client.force_login(customer)

    response = change(client, "customer123", "First@Example.com")

    assert response.url == reverse("accounts:security")
    customer.refresh_from_db()
    assert customer.email == "First@example.com"
    hub = client.get(response.url).content.decode()
    assert SUCCESS in hub
    assert "Add an email address to protect your account" not in hub
    assert mail.outbox == []


def test_change_acts_only_on_the_signed_in_user(client, customer, customer_with_email):
    client.force_login(customer)

    client.post(
        reverse("accounts:email_change"),
        {
            "current_password": "customer123",
            "email": "mine@example.com",
            "user": customer_with_email.pk,
            "username": "casey",
        },
    )

    customer.refresh_from_db()
    customer_with_email.refresh_from_db()
    assert customer.email == "mine@example.com"
    assert customer_with_email.email == "casey@example.com"


@pytest.mark.parametrize(
    ("who", "password"), [("staff_user", "employee123"), ("superuser", "admin123")]
)
def test_staff_and_superuser_can_change_email(client, request, who, password):
    user = request.getfixturevalue(who)
    client.force_login(user)

    assert client.get(reverse("accounts:email_change")).status_code == HTTPStatus.OK
    response = change(client, password, f"{user.username}-new@example.com")

    assert response.url == reverse("accounts:security")
    user.refresh_from_db()
    assert user.email == f"{user.username}-new@example.com"


def test_notice_method_is_a_no_op_without_an_old_address(customer_with_email):
    customer_with_email.send_email_changed_notice("")

    assert mail.outbox == []


@pytest.mark.parametrize(
    ("address", "masked"),
    [
        ("sam@example.com", "s***@example.com"),
        ("a@example.com", "a***@example.com"),
        ("Sam.Smith@mail.example.com", "S***@mail.example.com"),
    ],
)
def test_mask_email(address, masked):
    assert mask_email(address) == masked
    assert mask_email(address) != address
