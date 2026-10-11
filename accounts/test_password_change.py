"""Changing a password from the Security Center, and its notification."""

import re
from http import HTTPStatus

import pytest
from django.core import mail
from django.test import Client
from django.urls import reverse

NEW_PASSWORD = "Fresh-Thoughts-2026"
# Django reset tokens look like "<base36 timestamp>-<20+ hex chars>".
TOKEN_SHAPE = re.compile(r"\b[0-9a-z]{1,13}-[0-9a-f]{20,}\b")


def change(client, old, new1=NEW_PASSWORD, new2=None):
    return client.post(
        reverse("accounts:password_change"),
        {"old_password": old, "new_password1": new1, "new_password2": new2 or new1},
    )


def test_password_change_lives_under_security():
    assert reverse("accounts:password_change") == "/accounts/security/password/"


def test_signed_out_visitor_is_sent_to_sign_in_with_next(client, db):
    response = client.get(reverse("accounts:password_change"))

    assert response.status_code == HTTPStatus.FOUND
    assert (
        response.url == f"{reverse('accounts:login')}?next=/accounts/security/password/"
    )


def test_hub_links_to_password_change(client, customer):
    client.force_login(customer)

    page = client.get(reverse("accounts:security")).content.decode()

    assert reverse("accounts:password_change") in page


def test_wrong_current_password_is_rejected(client, customer_with_email):
    client.force_login(customer_with_email)

    response = change(client, "not-my-password")

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["old_password"]
    customer_with_email.refresh_from_db()
    assert customer_with_email.check_password("casey12345")
    assert mail.outbox == []


@pytest.mark.parametrize(
    ("new1", "new2"),
    [
        ("short", "short"),  # too short
        ("password123", "password123"),  # too common
        ("83920571634", "83920571634"),  # entirely numeric
        (NEW_PASSWORD, "Something-Else-2026"),  # mismatch
    ],
)
def test_invalid_new_password_is_rejected(client, customer_with_email, new1, new2):
    client.force_login(customer_with_email)

    response = change(client, "casey12345", new1, new2)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["new_password2"]
    customer_with_email.refresh_from_db()
    assert customer_with_email.check_password("casey12345")
    assert mail.outbox == []


def test_valid_change_keeps_this_session_and_returns_to_hub(
    client, customer_with_email
):
    client.force_login(customer_with_email)

    response = change(client, "casey12345")

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:security")
    customer_with_email.refresh_from_db()
    assert customer_with_email.check_password(NEW_PASSWORD)

    hub = client.get(response.url)
    assert hub.context["user"].is_authenticated
    assert hub.context["user"] == customer_with_email
    assert "Your password has been changed." in hub.content.decode()


def test_valid_change_signs_out_other_sessions(client, customer_with_email):
    other_device = Client()
    other_device.force_login(customer_with_email)
    assert other_device.get(reverse("accounts:security")).status_code == HTTPStatus.OK
    client.force_login(customer_with_email)

    change(client, "casey12345")

    response = other_device.get(reverse("accounts:security"))
    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))
    assert client.get(reverse("accounts:security")).status_code == HTTPStatus.OK


def test_valid_change_sends_one_safe_notification(
    client, settings, customer_with_email
):
    client.force_login(customer_with_email)

    change(client, "casey12345")

    assert len(mail.outbox) == 1
    message = mail.outbox[0]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert message.to == ["casey@example.com"]
    body = message.body
    assert "casey" in body
    assert "UTC" in body
    assert "Forgot your password?" in body
    assert NEW_PASSWORD not in body
    assert "casey12345" not in body
    assert "http" not in body
    assert not TOKEN_SHAPE.search(body)


def test_user_without_email_changes_password_and_gets_no_mail(client, customer):
    client.force_login(customer)

    response = change(client, "customer123")

    assert response.url == reverse("accounts:security")
    customer.refresh_from_db()
    assert customer.check_password(NEW_PASSWORD)
    assert (
        "Your password has been changed." in client.get(response.url).content.decode()
    )
    assert mail.outbox == []


@pytest.mark.parametrize(
    ("who", "old"), [("staff_user", "employee123"), ("superuser", "admin123")]
)
def test_staff_and_superuser_can_change_password(client, request, who, old):
    user = request.getfixturevalue(who)
    client.force_login(user)

    assert client.get(reverse("accounts:password_change")).status_code == HTTPStatus.OK
    response = change(client, old)

    assert response.url == reverse("accounts:security")
    user.refresh_from_db()
    assert user.check_password(NEW_PASSWORD)


def test_notification_method_is_a_no_op_without_email(customer):
    customer.send_password_changed_notification()

    assert mail.outbox == []


def test_notification_method_uses_default_from_email(settings, customer_with_email):
    settings.DEFAULT_FROM_EMAIL = "Test Sender <sender@example.com>"

    customer_with_email.send_password_changed_notification()

    assert mail.outbox[0].from_email == "Test Sender <sender@example.com>"
