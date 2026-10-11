"""The auth-aware navbar."""

from django.urls import reverse


def test_navbar_offers_login_and_signup_to_visitors(client, db):
    page = client.get(reverse("products:catalog")).content.decode()

    assert reverse("accounts:login") in page
    assert reverse("accounts:signup") in page
    assert "Sign out" not in page


def test_navbar_greets_signed_in_customer(client, customer):
    client.force_login(customer)

    page = client.get(reverse("products:catalog")).content.decode()

    assert "Hi, customer" in page
    assert "Sign out" in page
    assert reverse("accounts:signup") not in page


def test_navbar_greeting_links_to_security_center(client, customer):
    client.force_login(customer)

    page = client.get(reverse("products:catalog")).content.decode()

    assert f'href="{reverse("accounts:security")}"' in page
