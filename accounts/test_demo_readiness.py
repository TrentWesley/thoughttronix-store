"""Definition of done: the migration and every Security Center page."""

from http import HTTPStatus

import pytest
from django.db import connection
from django.db.migrations.executor import MigrationExecutor
from django.urls import reverse

BEFORE = [("accounts", "0001_initial")]
AFTER = [("accounts", "0002_email_ci_unique")]


@pytest.mark.django_db(transaction=True)
def test_email_constraint_migrates_a_database_with_blank_emails():
    executor = MigrationExecutor(connection)
    executor.migrate(BEFORE)
    OldUser = executor.loader.project_state(BEFORE).apps.get_model("accounts", "User")
    for username in ("blank1", "blank2", "blank3"):
        OldUser.objects.create(username=username, email="")
    OldUser.objects.create(username="emailed", email="emailed@example.com")

    executor.loader.build_graph()
    executor.migrate(AFTER)

    NewUser = executor.loader.project_state(AFTER).apps.get_model("accounts", "User")
    assert NewUser.objects.filter(email="").count() == 3
    assert NewUser.objects.count() == 4


@pytest.mark.parametrize(
    "name",
    ["security", "password_change", "email_change"],
)
def test_signed_in_pages_render(client, customer, name):
    client.force_login(customer)

    response = client.get(reverse(f"accounts:{name}"))

    assert response.status_code == HTTPStatus.OK


@pytest.mark.parametrize(
    "name",
    ["password_reset", "password_reset_done", "password_reset_complete"],
)
def test_public_pages_render(client, db, name):
    response = client.get(reverse(f"accounts:{name}"))

    assert response.status_code == HTTPStatus.OK


def test_bad_reset_link_renders_the_invalid_link_page(client, db):
    url = reverse("accounts:password_reset_confirm", args=["MQ", "bad-token"])

    response = client.get(url)

    assert response.status_code == HTTPStatus.OK
    assert not response.context["validlink"]
    assert "This reset link doesn't work" in response.content.decode()
