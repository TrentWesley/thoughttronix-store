"""Deleting a review in place: the inline confirmation, Confirm Delete and
Cancel, the form slot afterward, and ownership enforced by the lookup."""

import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from orders.models import Order

from .models import Review

HTMX = {"HX-Request": "true"}
ORIGINAL = "The original words, exactly as posted."
CONFIRM_TEXT = "Delete this review? This can't be undone."


def confirm_url(review):
    return reverse("reviews:delete_confirm", kwargs={"pk": review.pk})


def delete_url(review):
    return reverse("reviews:delete", kwargs={"pk": review.pk})


def cancel_url(review):
    return reverse("reviews:cancel_delete", kwargs={"pk": review.pk})


def create_url(product):
    return reverse("reviews:create", kwargs={"pk": product.pk})


def template_names(response):
    return [template.name for template in response.templates]


def has_oob_summary(html):
    return re.search(r'id="review-summary"[^>]*hx-swap-oob="true"', html) is not None


def without_oob_summary(html):
    """The response minus its out-of-band summary: what swaps into the target."""
    return re.sub(
        r'<div id="review-summary"[^>]*hx-swap-oob="true"[^>]*>.*\Z',
        "",
        html,
        flags=re.DOTALL,
    )


def page_of(client, product):
    response = client.get(product.get_absolute_url())
    assert response.status_code == HTTPStatus.OK
    return response.content.decode()


def card_html(page, review):
    """The markup of one review card, up to its closing ``</article>``."""
    start = page.index(f'id="review-{review.pk}"')
    return page[start : page.index("</article>", start)]


@pytest.fixture
def review(customer, product, make_review):
    """The customer's own 4-star review, posted a week ago."""
    return make_review(
        customer,
        product,
        rating=4,
        comment=ORIGINAL,
        created_at=timezone.now() - timedelta(days=7),
    )


# --- Delete buttons ----------------------------------------------------------


def test_author_sees_delete_on_their_own_review(client, customer, review):
    client.force_login(customer)

    card = card_html(page_of(client, review.product), review)

    assert f'hx-get="{confirm_url(review)}"' in card
    assert f'hx-target="#review-{review.pk}"' in card


def test_staff_see_delete_on_every_review(client, staff_user, review):
    client.force_login(staff_user)

    card = card_html(page_of(client, review.product), review)

    assert f'hx-get="{confirm_url(review)}"' in card


def test_no_delete_on_other_customers_reviews(client, named_customer, review):
    client.force_login(named_customer)

    assert confirm_url(review) not in page_of(client, review.product)


def test_no_delete_for_signed_out_visitors(client, review):
    assert confirm_url(review) not in page_of(client, review.product)


# --- Confirmation and Cancel ------------------------------------------------


def test_confirmation_replaces_the_card_and_changes_nothing(client, customer, review):
    client.force_login(customer)

    response = client.get(confirm_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    names = template_names(response)
    assert "reviews/partials/_delete_confirm.html" in names
    assert "base.html" not in names
    html = response.content.decode()
    assert f'id="review-{review.pk}"' in html
    assert CONFIRM_TEXT in html
    assert "Confirm Delete" in html
    assert f'hx-post="{delete_url(review)}"' in html
    assert f'hx-get="{cancel_url(review)}"' in html
    assert "hx-disabled-elt=" in html
    assert Review.objects.filter(pk=review.pk).exists()


def test_cancel_returns_the_unchanged_card(client, customer, review):
    client.force_login(customer)

    response = client.get(cancel_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert "reviews/partials/_review_card.html" in template_names(response)
    html = response.content.decode()
    assert f'id="review-{review.pk}"' in html
    assert ORIGINAL in html
    assert "Confirm Delete" not in html
    assert not has_oob_summary(html)
    assert Review.objects.filter(pk=review.pk).exists()


@pytest.mark.parametrize("url", [confirm_url, cancel_url])
def test_delete_is_post_only_and_the_others_get_only(client, customer, review, url):
    client.force_login(customer)

    assert client.get(delete_url(review), headers=HTMX).status_code == 405
    assert client.post(url(review), headers=HTMX).status_code == 405
    assert Review.objects.filter(pk=review.pk).exists()


# --- Confirm Delete ----------------------------------------------------------


def test_staff_delete_removes_the_card_and_refreshes_the_summary(
    client, staff_user, named_customer, review, make_review
):
    make_review(named_customer, review.product, rating=2)
    client.force_login(staff_user)

    response = client.post(delete_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert not Review.objects.filter(pk=review.pk).exists()
    assert "base.html" not in template_names(response)
    html = response.content.decode()
    assert has_oob_summary(html)
    assert "2.0 out of 5" in html
    assert "1 review" in html
    # Nothing else: the empty body swaps over the card, removing it.
    assert without_oob_summary(html).strip() == ""
    assert "HX-Retarget" not in response


def test_deleting_the_last_review_shows_no_reviews_yet(client, staff_user, review):
    client.force_login(staff_user)

    response = client.post(delete_url(review), headers=HTMX)

    html = response.content.decode()
    assert has_oob_summary(html)
    assert "No reviews yet" in html


def test_author_delete_rerenders_the_slot_with_the_form_when_still_eligible(
    client, customer, product, delivered_order, review
):
    delivered_order(customer, product)
    client.force_login(customer)

    response = client.post(delete_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert not Review.objects.filter(pk=review.pk).exists()
    assert response["HX-Retarget"] == "#review-form-slot"
    assert response["HX-Reswap"] == "innerHTML"
    names = template_names(response)
    assert "reviews/partials/_form_slot.html" in names
    assert "reviews/partials/_review_form.html" in names
    html = response.content.decode()
    assert f'hx-post="{create_url(product)}"' in html
    assert ORIGINAL not in html
    assert has_oob_summary(html)
    assert "No reviews yet" in html


def test_author_delete_shows_not_eligible_once_the_order_is_cancelled(
    client, customer, product, delivered_order, review
):
    order = delivered_order(customer, product)
    order.status = Order.Status.CANCELLED
    order.save()
    client.force_login(customer)

    response = client.post(delete_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert not Review.objects.filter(pk=review.pk).exists()
    assert response["HX-Retarget"] == "#review-form-slot"
    html = response.content.decode()
    assert "Only customers with a delivered order can review this product." in html
    assert create_url(product) not in html
    assert has_oob_summary(html)


def test_after_delete_the_product_page_offers_the_form_again(
    client, customer, product, delivered_order, review
):
    delivered_order(customer, product)
    client.force_login(customer)

    client.post(delete_url(review), headers=HTMX)

    page = page_of(client, product)
    assert f'hx-post="{create_url(product)}"' in page
    assert ORIGINAL not in page


def test_staff_deleting_their_own_review_rerenders_their_slot(
    client, staff_user, product, delivered_order, make_review
):
    delivered_order(staff_user, product)
    own = make_review(staff_user, product, comment=ORIGINAL)
    client.force_login(staff_user)

    response = client.post(delete_url(own), headers=HTMX)

    assert not Review.objects.filter(pk=own.pk).exists()
    assert response["HX-Retarget"] == "#review-form-slot"
    assert f'hx-post="{create_url(product)}"' in response.content.decode()


def test_author_can_delete_after_their_order_is_cancelled(
    client, customer, product, delivered_order, review
):
    order = delivered_order(customer, product)
    order.status = Order.Status.CANCELLED
    order.save()
    client.force_login(customer)

    assert client.get(confirm_url(review), headers=HTMX).status_code == HTTPStatus.OK
    response = client.post(delete_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert not Review.objects.filter(pk=review.pk).exists()


# --- Ownership is enforced by the lookup ------------------------------------


def assert_review_alert(response, review):
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response["HX-Retarget"] == f"#review-{review.pk}"
    assert response["HX-Reswap"] == "outerHTML"
    assert "reviews/partials/_alert.html" in template_names(response)
    html = response.content.decode()
    assert 'role="alert"' in html
    assert "This review is no longer available." in html
    return html


def test_another_customer_gets_404_for_the_confirmation(client, named_customer, review):
    client.force_login(named_customer)

    html = assert_review_alert(client.get(confirm_url(review), headers=HTMX), review)

    assert "Confirm Delete" not in html
    assert Review.objects.filter(pk=review.pk).exists()


def test_another_customer_gets_404_for_the_delete_and_the_review_stays(
    client, named_customer, review
):
    client.force_login(named_customer)

    assert_review_alert(client.post(delete_url(review), headers=HTMX), review)

    assert Review.objects.filter(pk=review.pk).exists()


def test_another_customer_gets_404_for_cancel(client, named_customer, review):
    client.force_login(named_customer)

    assert_review_alert(client.get(cancel_url(review), headers=HTMX), review)


def test_deleting_an_already_deleted_review_is_404_with_an_alert(
    client, customer, review
):
    client.force_login(customer)
    deleted = Review(pk=review.pk)
    review.delete()

    assert_review_alert(client.get(confirm_url(deleted), headers=HTMX), deleted)
    assert_review_alert(client.post(delete_url(deleted), headers=HTMX), deleted)


# --- Signed-out requests ------------------------------------------------------


def login_with_next(product):
    return f"{reverse('accounts:login')}?next={product.get_absolute_url()}"


def test_anonymous_htmx_delete_gets_hx_redirect_and_deletes_nothing(client, review):
    response = client.post(delete_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response["HX-Redirect"] == login_with_next(review.product)
    assert Review.objects.filter(pk=review.pk).exists()


def test_anonymous_plain_confirmation_gets_the_normal_login_redirect(client, review):
    response = client.get(confirm_url(review))

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == login_with_next(review.product)
