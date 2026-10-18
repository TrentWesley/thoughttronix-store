"""A stale CSRF token on a review action: signing in at another tab.

``base.html`` renders the CSRF token into ``hx-headers`` once, at page
load. Signing in rotates the token (``django.contrib.auth.login`` calls
``rotate_token``) and the cookie is shared by every tab, so an open
product page's token goes stale. The product page's ``htmx-config``
swaps 403s, so a review action must answer that failure with the inline
alert — never Django's CSRF error page squeezed into a card.
"""

import re
from http import HTTPStatus

import pytest
from django.test import Client
from django.urls import reverse

from .models import Review

HTMX = {"HX-Request": "true"}
STALE = "Your session changed in another tab. Refresh the page and try again."
TOKEN = re.compile(r'"X-CSRFToken": "([^"]+)"')


def page_token(client, url) -> str:
    """The CSRF token a page embeds for HTMX, as the browser would send it."""
    response = client.get(url)
    assert response.status_code == HTTPStatus.OK
    return TOKEN.search(response.content.decode()).group(1)


@pytest.fixture
def browser():
    return Client(enforce_csrf_checks=True)


@pytest.fixture
def review(customer, product, make_review):
    return make_review(customer, product, comment="Words worth keeping around.")


@pytest.fixture
def stale_token(browser, customer, superuser, review):
    """Open the product page as ``customer``, then sign in as admin in a
    "second tab" (same cookies). Returns the first tab's now-stale token."""
    browser.force_login(customer)
    old = page_token(browser, review.product.get_absolute_url())
    login = reverse("accounts:login")
    response = browser.post(
        login,
        {"username": "admin", "password": "admin123"},
        headers={"X-CSRFToken": page_token(browser, login)},
    )
    assert response.status_code == HTTPStatus.FOUND
    return old


def assert_stale_alert(response, target, swap):
    assert response.status_code == HTTPStatus.FORBIDDEN
    assert response["HX-Retarget"] == target
    assert response["HX-Reswap"] == swap
    assert "reviews/partials/_alert.html" in [t.name for t in response.templates]
    html = response.content.decode()
    assert 'role="alert"' in html
    assert STALE in html
    assert "CSRF verification failed" not in html
    assert "<html" not in html


def test_signing_in_elsewhere_makes_the_open_pages_token_stale(
    browser, review, stale_token
):
    """The root cause: after rotation the old token is rejected."""
    response = browser.post(
        reverse("reviews:delete", kwargs={"pk": review.pk}),
        headers={"X-CSRFToken": stale_token},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert Review.objects.filter(pk=review.pk).exists()


def test_stale_token_on_confirm_delete_gets_the_inline_alert(
    browser, review, stale_token
):
    response = browser.post(
        reverse("reviews:delete", kwargs={"pk": review.pk}),
        headers={**HTMX, "X-CSRFToken": stale_token},
    )

    assert_stale_alert(response, f"#review-{review.pk}", "outerHTML")
    assert Review.objects.filter(pk=review.pk).exists()


def test_stale_token_on_a_review_deleted_elsewhere_still_gets_the_alert(
    browser, review, stale_token
):
    """Test 5: the review was deleted in the admin tab, then Confirm Delete."""
    pk = review.pk
    review.delete()

    response = browser.post(
        reverse("reviews:delete", kwargs={"pk": pk}),
        headers={**HTMX, "X-CSRFToken": stale_token},
    )

    assert_stale_alert(response, f"#review-{pk}", "outerHTML")


def test_stale_token_on_update_gets_the_inline_alert(browser, review, stale_token):
    response = browser.post(
        reverse("reviews:update", kwargs={"pk": review.pk}),
        {"rating": "1", "comment": "Changed by a stale tab."},
        headers={**HTMX, "X-CSRFToken": stale_token},
    )

    assert_stale_alert(response, f"#review-{review.pk}", "outerHTML")
    review.refresh_from_db()
    assert review.comment == "Words worth keeping around."


def test_stale_token_on_create_alerts_in_the_form_slot(
    browser, customer, other_product, stale_token
):
    response = browser.post(
        reverse("reviews:create", kwargs={"pk": other_product.pk}),
        {"rating": "5", "comment": "Posted from a stale tab."},
        headers={**HTMX, "X-CSRFToken": stale_token},
    )

    assert_stale_alert(response, "#review-form-slot", "innerHTML")
    assert not Review.objects.filter(product=other_product).exists()


def test_after_a_refresh_the_new_token_works(browser, review, stale_token):
    """The retest path: refreshing picks up the rotated token. The tab is
    now signed in as admin (staff), so the delete goes through."""
    fresh = page_token(browser, review.product.get_absolute_url())

    response = browser.post(
        reverse("reviews:delete", kwargs={"pk": review.pk}),
        headers={**HTMX, "X-CSRFToken": fresh},
    )

    assert response.status_code == HTTPStatus.OK
    assert not Review.objects.filter(pk=review.pk).exists()


def test_non_htmx_review_post_keeps_djangos_csrf_page(browser, review, stale_token):
    response = browser.post(
        reverse("reviews:delete", kwargs={"pk": review.pk}),
        headers={"X-CSRFToken": stale_token},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "HX-Retarget" not in response
    assert "CSRF verification failed" in response.content.decode()


def test_other_htmx_endpoints_keep_djangos_csrf_page(browser, product, stale_token):
    """Only review endpoints change; the cart keeps Django's default."""
    response = browser.post(
        reverse("orders:add", kwargs={"pk": product.pk}),
        headers={**HTMX, "X-CSRFToken": stale_token},
    )

    assert response.status_code == HTTPStatus.FORBIDDEN
    assert "HX-Retarget" not in response
    assert "CSRF verification failed" in response.content.decode()
