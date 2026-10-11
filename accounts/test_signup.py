"""The signup page."""

from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.urls import reverse


def test_signup_page_returns_200(client, db):
    response = client.get(reverse("accounts:signup"))

    assert response.status_code == HTTPStatus.OK


def test_signup_creates_plain_customer(client, db):
    response = client.post(
        reverse("accounts:signup"),
        {
            "username": "fresh-thinker",
            "email": "fresh@example.com",
            "password1": "neural-implant-9000",
            "password2": "neural-implant-9000",
        },
        follow=True,
    )

    user = get_user_model().objects.get(username="fresh-thinker")
    assert not user.is_staff
    assert not user.is_superuser

    # Signup hands off to the login page with a confirmation message;
    # auto-login is a student exercise, so the visitor is still anonymous.
    assert response.redirect_chain[-1][0] == reverse("accounts:login")
    assert "Account created" in response.content.decode()
    assert not response.context["user"].is_authenticated


def test_signup_password_mismatch_shows_field_error(client, db):
    response = client.post(
        reverse("accounts:signup"),
        {
            "username": "fresh-thinker",
            "email": "fresh@example.com",
            "password1": "neural-implant-9000",
            "password2": "neural-implant-9001",
        },
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["password2"]
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()


def signup(client, email, username="fresh-thinker"):
    data = {
        "username": username,
        "password1": "neural-implant-9000",
        "password2": "neural-implant-9000",
    }
    if email is not None:
        data["email"] = email
    return client.post(reverse("accounts:signup"), data)


def test_signup_page_shows_email_field(client, db):
    response = client.get(reverse("accounts:signup"))

    page = response.content.decode()
    assert 'name="email"' in page
    assert response.context["form"].fields["email"].required


def test_signup_without_email_fails(client, db):
    response = signup(client, email=None)

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"]
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()


def test_signup_with_blank_email_fails(client, db):
    response = signup(client, email="   ")

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["email"]
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()


def test_signup_normalizes_email(client, db):
    response = signup(client, email="  Sam@Example.COM  ")

    assert response.status_code == HTTPStatus.FOUND
    user = get_user_model().objects.get(username="fresh-thinker")
    assert user.email == "Sam@example.com"


def test_signup_rejects_case_variant_duplicate_email(client, customer_with_email):
    response = signup(client, email="  CASEY@Example.com ")

    assert response.status_code == HTTPStatus.OK
    form = response.context["form"]
    assert form.errors["email"] == [
        "That email address already belongs to another account."
    ]
    # The database constraint's own message stays out of the way.
    assert not form.non_field_errors()
    assert not get_user_model().objects.filter(username="fresh-thinker").exists()
