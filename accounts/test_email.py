"""The recovery email: normalization and database-level uniqueness."""

import pytest
from django.contrib.auth import get_user_model
from django.db import IntegrityError, transaction


@pytest.mark.parametrize(
    ("typed", "stored"),
    [
        ("  sam@example.com  ", "sam@example.com"),
        ("\tsam@example.com\n", "sam@example.com"),
        ("sam@EXAMPLE.Com", "sam@example.com"),
        ("Sam.Smith@Example.COM", "Sam.Smith@example.com"),
        ("  SAM@Example.COM ", "SAM@example.com"),
    ],
)
def test_normalize_recovery_email(typed, stored):
    assert get_user_model().normalize_recovery_email(typed) == stored


@pytest.mark.parametrize("typed", ["", "   ", None])
def test_normalize_recovery_email_blank_stays_blank(typed):
    assert get_user_model().normalize_recovery_email(typed) == ""


def test_database_rejects_case_variant_duplicate_email(db):
    User = get_user_model()
    User.objects.create_user(username="first", email="sam@example.com")

    # Bypass every form: the constraint alone must hold the line.
    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.create(username="second", email="SAM@Example.com")

    assert not User.objects.filter(username="second").exists()


def test_database_rejects_case_variant_duplicate_on_update(db):
    User = get_user_model()
    User.objects.create_user(username="first", email="sam@example.com")
    second = User.objects.create_user(username="second", email="other@example.com")

    with pytest.raises(IntegrityError), transaction.atomic():
        User.objects.filter(pk=second.pk).update(email="Sam@EXAMPLE.com")


def test_many_blank_emails_coexist(db):
    User = get_user_model()
    for username in ("blank-one", "blank-two", "blank-three"):
        User.objects.create_user(username=username, email="")

    assert User.objects.filter(email="").count() == 3
