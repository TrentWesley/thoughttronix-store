"""The public forgot-password flow."""

import re
from http import HTTPStatus

import pytest
from django.conf import global_settings
from django.contrib.auth import get_user_model
from django.core import mail
from django.test import Client
from django.urls import resolve, reverse

NEW_PASSWORD = "Fresh-Thoughts-2026"
RESET_LINK = re.compile(r"http://testserver(/accounts/reset/\S+/)")
# Django reset tokens look like "<base36 timestamp>-<20+ hex chars>".
TOKEN_SHAPE = re.compile(r"\b[0-9a-z]{1,13}-[0-9a-f]{20,}\b")
# base.html embeds a per-session CSRF token for HTMX; mask it to compare pages.
CSRF_VALUE = re.compile(r'"X-CSRFToken": "[^"]+"')


def without_csrf(page):
    return CSRF_VALUE.sub('"X-CSRFToken": ""', page)


def request_reset(client, email):
    return client.post(reverse("accounts:password_reset"), {"email": email})


def reset_link(message):
    match = RESET_LINK.search(message.body)
    assert match, message.body
    return match.group(1)


def set_new_password(client, link, password=NEW_PASSWORD):
    """Follow a reset link and submit a new password, as a browser would."""
    response = client.get(link)
    assert response.status_code == HTTPStatus.FOUND  # to the set-password URL
    return client.post(
        response.url, {"new_password1": password, "new_password2": password}
    )


@pytest.fixture
def reset_email(client, customer_with_email):
    request_reset(client, "casey@example.com")
    return mail.outbox.pop()


def test_reset_routes_live_at_the_prd_paths():
    assert reverse("accounts:password_reset") == "/accounts/password-reset/"
    assert reverse("accounts:password_reset_done") == "/accounts/password-reset/sent/"
    assert reverse("accounts:password_reset_complete") == "/accounts/reset/complete/"
    assert (
        reverse("accounts:password_reset_confirm", args=["MQ", "abc-123"])
        == "/accounts/reset/MQ/abc-123/"
    )


def test_sign_in_page_links_to_forgot_password(client, db):
    page = client.get(reverse("accounts:login")).content.decode()

    assert f'href="{reverse("accounts:password_reset")}"' in page
    assert "Forgot your password?" in page


def test_forgot_password_page_is_public(client, db):
    assert client.get(reverse("accounts:password_reset")).status_code == HTTPStatus.OK


def test_reset_timeout_is_djangos_three_day_default(settings):
    assert settings.PASSWORD_RESET_TIMEOUT == global_settings.PASSWORD_RESET_TIMEOUT
    assert settings.PASSWORD_RESET_TIMEOUT == 60 * 60 * 24 * 3


@pytest.fixture
def every_kind_of_account(customer, customer_with_email):
    """Blank-email, emailed, inactive, and unusable-password accounts."""
    User = get_user_model()
    User.objects.create_user(username="blank2", password="blank12345")
    User.objects.create_user(
        username="dormant",
        password="dormant12345",
        email="dormant@example.com",
        is_active=False,
    )
    User.objects.create_user(username="nopass", email="nopass@example.com")


@pytest.mark.parametrize(
    ("email", "sends"),
    [
        ("casey@example.com", True),  # known
        ("CASEY@Example.COM", True),  # case-variant of known
        ("nobody@example.com", False),  # unknown, while blank-email accounts exist
        ("dormant@example.com", False),  # inactive
        ("nopass@example.com", False),  # unusable password
    ],
)
def test_every_case_gets_the_same_confirmation(
    client, every_kind_of_account, email, sends
):
    response = request_reset(client, email)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:password_reset_done")
    page = without_csrf(client.get(response.url).content.decode())
    baseline = Client().get(reverse("accounts:password_reset_done")).content.decode()
    assert page == without_csrf(baseline)
    assert "If an account matches" in page
    assert len(mail.outbox) == (1 if sends else 0)


def test_reset_email_is_branded_and_links_to_the_namespaced_confirm(
    client, settings, customer_with_email
):
    request_reset(client, "CASEY@example.com")

    (message,) = mail.outbox
    assert message.to == ["casey@example.com"]
    assert message.from_email == settings.DEFAULT_FROM_EMAIL
    assert "ThoughtTronix Store" in message.subject
    assert "ThoughtTronix Store" in message.body
    assert "casey" in message.body
    assert message.alternatives == []  # plain text only
    match = resolve(reset_link(message))
    assert match.view_name == "accounts:password_reset_confirm"


def test_valid_link_sets_a_new_password(client, customer_with_email, reset_email):
    response = set_new_password(client, reset_link(reset_email))

    assert response.status_code == HTTPStatus.FOUND
    assert response.url == reverse("accounts:password_reset_complete")
    customer_with_email.refresh_from_db()
    assert customer_with_email.check_password(NEW_PASSWORD)


@pytest.mark.parametrize("weak", ["short", "password123", "83920571634"])
def test_weak_new_password_is_rejected(client, customer_with_email, reset_email, weak):
    response = set_new_password(client, reset_link(reset_email), weak)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["new_password2"]
    customer_with_email.refresh_from_db()
    assert customer_with_email.check_password("casey12345")
    assert mail.outbox == []


def test_completion_does_not_sign_in_and_links_to_sign_in(
    client, customer_with_email, reset_email
):
    response = set_new_password(client, reset_link(reset_email))

    complete = client.get(response.url)
    assert complete.status_code == HTTPStatus.OK
    assert not complete.context["user"].is_authenticated
    page = complete.content.decode()
    assert "Password reset complete" in page
    assert f'href="{reverse("accounts:login")}"' in page

    signed_in = client.post(
        reverse("accounts:login"),
        {"username": "casey", "password": NEW_PASSWORD},
    )
    assert signed_in.status_code == HTTPStatus.FOUND
    assert client.get(reverse("accounts:security")).status_code == HTTPStatus.OK


def test_completion_sends_the_safe_password_changed_notification(
    client, customer_with_email, reset_email
):
    set_new_password(client, reset_link(reset_email))

    (message,) = mail.outbox
    assert message.to == ["casey@example.com"]
    assert message.subject == "Your ThoughtTronix Store password was changed"
    body = message.body
    assert "UTC" in body
    assert "Forgot your password?" in body
    assert NEW_PASSWORD not in body
    assert "http" not in body
    assert not TOKEN_SHAPE.search(body)


def test_used_link_cannot_be_reused(client, customer_with_email, reset_email):
    link = reset_link(reset_email)
    set_new_password(client, link)

    attacker = Client()
    response = attacker.get(link, follow=True)
    assert response.status_code == HTTPStatus.OK
    assert response.context["validlink"] is False
    assert "This reset link doesn't work" in response.content.decode()

    attacker.post(
        link,
        {"new_password1": "Another-Pass-2026", "new_password2": "Another-Pass-2026"},
    )
    customer_with_email.refresh_from_db()
    assert customer_with_email.check_password(NEW_PASSWORD)
