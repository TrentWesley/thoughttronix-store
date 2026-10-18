"""Writing a review in place: the form slot, the create endpoint, and the
HTMX error machinery (inline alerts, page-scoped config, HX-Redirect)."""

import json
import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from orders.models import Order

from .models import Review

HTMX = {"HX-Request": "true"}
VALID = {"rating": "5", "comment": "Seraphine finished my sentences."}


def create_url(product):
    return reverse("reviews:create", kwargs={"pk": product.pk})


def post_review(client, product, **data):
    return client.post(create_url(product), {**VALID, **data}, headers=HTMX)


def page_of(client, product):
    response = client.get(product.get_absolute_url())
    assert response.status_code == HTTPStatus.OK
    return response.content.decode()


def template_names(response):
    return [template.name for template in response.templates]


def has_oob_summary(html):
    return re.search(r'id="review-summary"[^>]*hx-swap-oob="true"', html) is not None


def login_with_next(product):
    return f"{reverse('accounts:login')}?next={product.get_absolute_url()}"


# --- The form slot on the product page ---------------------------------------


def test_signed_out_slot_links_to_sign_in_and_back(client, product):
    page = page_of(client, product)

    assert 'id="review-form-slot"' in page
    assert "Sign in to review products you've purchased" in page
    assert f'href="{login_with_next(product)}"' in page
    assert create_url(product) not in page


def test_slot_explains_why_a_customer_without_a_delivery_cannot_review(
    client, customer, product
):
    client.force_login(customer)

    page = page_of(client, product)

    assert "Only customers with a delivered order can review this product" in page
    assert create_url(product) not in page


@pytest.mark.parametrize("status", [Order.Status.PLACED, Order.Status.SHIPPED])
def test_slot_tells_a_customer_with_an_undelivered_order_to_wait(
    client, customer, product, delivered_order, status
):
    delivered_order(customer, product, status=status)
    client.force_login(customer)

    page = page_of(client, product)

    assert "Only customers with a delivered order can review this product" in page
    assert create_url(product) not in page


def test_slot_refuses_staff_without_a_purchase(client, staff_user, product):
    client.force_login(staff_user)

    page = page_of(client, product)

    assert "Only customers with a delivered order can review this product" in page
    assert create_url(product) not in page


def test_slot_shows_the_form_to_a_verified_purchaser(
    client, customer, product, delivered_order
):
    delivered_order(customer, product)
    client.force_login(customer)

    page = page_of(client, product)

    assert f'hx-post="{create_url(product)}"' in page
    assert 'hx-target="#review-form-slot"' in page
    assert "hx-disabled-elt=" in page
    for stars in range(1, 6):
        assert re.search(rf'type="radio" name="rating" value="{stars}"', page)
    assert 'name="comment"' in page


def test_slot_shows_the_form_for_an_unavailable_product(
    client, customer, unavailable_product, delivered_order
):
    delivered_order(customer, unavailable_product)
    client.force_login(customer)

    page = page_of(client, unavailable_product)

    assert f'hx-post="{create_url(unavailable_product)}"' in page


def test_own_review_is_pinned_once_and_replaces_the_form(
    client, customer, named_customer, product, delivered_order, make_review
):
    delivered_order(customer, product)
    now = timezone.now()
    mine = make_review(
        customer,
        product,
        comment="My own older review.",
        created_at=now - timedelta(days=9),
    )
    make_review(named_customer, product, comment="Someone else's newer review.")
    client.force_login(customer)

    page = page_of(client, product)

    assert page.count(f'id="review-{mine.pk}"') == 1
    assert page.index("My own older review.") < page.index("newer review.")
    assert page.index('id="review-form-slot"') < page.index(f'id="review-{mine.pk}"')
    assert create_url(product) not in page


def test_other_visitors_see_that_review_in_the_list_not_pinned(
    client, customer, product, make_review
):
    review = make_review(customer, product, comment="An ordinary list review.")

    page = page_of(client, product)

    assert page.count(f'id="review-{review.pk}"') == 1
    assert page.index('id="review-list"') < page.index(f'id="review-{review.pk}"')


# --- Page-scoped HTMX configuration -----------------------------------------


def htmx_config(page):
    match = re.search(r"<meta name=\"htmx-config\" content='([^']*)'", page)
    return json.loads(match.group(1)) if match else None


def test_product_page_carries_the_htmx_response_handling_config(client, product):
    config = htmx_config(page_of(client, product))

    assert config == {
        "responseHandling": [
            {"code": "204", "swap": False},
            {"code": "[23]..", "swap": True},
            {"code": "40[34]", "swap": True, "error": True},
            {"code": "[45]..", "swap": False, "error": True},
            {"code": "...", "swap": False},
        ]
    }


def test_catalog_keeps_htmx_defaults(client, product):
    response = client.get(reverse("products:catalog"))

    assert htmx_config(response.content.decode()) is None


def test_cart_keeps_htmx_defaults(client, customer):
    client.force_login(customer)

    response = client.get(reverse("orders:cart"))

    assert htmx_config(response.content.decode()) is None


# --- Creating a review -------------------------------------------------------


def test_create_saves_and_returns_the_pinned_card_with_the_summary_oob(
    client, customer, product, delivered_order
):
    delivered_order(customer, product)
    client.force_login(customer)

    response = post_review(client, product, comment="  She finished my sentences.  ")

    assert response.status_code == HTTPStatus.OK
    review = Review.objects.get()
    assert (review.user, review.product, review.rating) == (customer, product, 5)
    assert review.comment == "She finished my sentences."
    html = response.content.decode()
    assert f'id="review-{review.pk}"' in html
    assert "She finished my sentences." in html
    assert has_oob_summary(html)
    assert "5.0 out of 5" in html
    assert "1 review<" in html
    assert 'name="comment"' not in html


def test_create_renders_partials_never_the_base_template(
    client, customer, product, delivered_order
):
    delivered_order(customer, product)
    client.force_login(customer)

    response = post_review(client, product)

    names = template_names(response)
    assert "reviews/partials/_form_slot.html" in names
    assert "reviews/partials/_review_card.html" in names
    assert "base.html" not in names


def test_created_comment_is_autoescaped(client, customer, product, delivered_order):
    delivered_order(customer, product)
    client.force_login(customer)

    response = post_review(client, product, comment="<script>alert('x')</script>")

    html = response.content.decode()
    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_a_verified_purchaser_can_review_an_unavailable_product(
    client, customer, unavailable_product, delivered_order
):
    delivered_order(customer, unavailable_product)
    client.force_login(customer)

    response = post_review(client, unavailable_product)

    assert response.status_code == HTTPStatus.OK
    assert Review.objects.filter(product=unavailable_product).count() == 1


def test_invalid_create_rerenders_the_form_with_errors_and_typed_values(
    client, customer, product, delivered_order
):
    delivered_order(customer, product)
    client.force_login(customer)

    response = post_review(client, product, rating="4", comment="Too short")

    assert response.status_code == HTTPStatus.OK
    assert not Review.objects.exists()
    html = response.content.decode()
    assert "Ensure this value has at least 10 characters" in html
    assert "Too short" in html
    assert re.search(r'value="4"[^>]*checked', html)
    assert 'name="comment"' in html
    assert not has_oob_summary(html)
    assert "reviews/partials/_review_form.html" in template_names(response)


def test_missing_rating_is_a_field_error(client, customer, product, delivered_order):
    delivered_order(customer, product)
    client.force_login(customer)

    response = post_review(client, product, rating="")

    assert response.status_code == HTTPStatus.OK
    assert not Review.objects.exists()
    html = response.content.decode()
    assert "This field is required." in html
    assert "Seraphine finished my sentences." in html


def test_create_is_post_only(client, customer, product, delivered_order):
    delivered_order(customer, product)
    client.force_login(customer)

    response = client.get(create_url(product), headers=HTMX)

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED
    assert not Review.objects.exists()


# --- Refusals: 403 and 404 with an inline alert -----------------------------


def assert_inline_alert(response, status):
    assert response.status_code == status
    assert response["HX-Retarget"] == "#review-form-slot"
    assert response["HX-Reswap"] == "innerHTML"
    html = response.content.decode()
    assert 'role="alert"' in html
    assert "reviews/partials/_alert.html" in template_names(response)
    return html


def test_ineligible_create_is_403_with_an_alert_and_saves_nothing(
    client, customer, product
):
    client.force_login(customer)

    response = post_review(client, product)

    html = assert_inline_alert(response, HTTPStatus.FORBIDDEN)
    assert "delivered order" in html
    assert has_oob_summary(html)
    assert not Review.objects.exists()


@pytest.mark.parametrize(
    "status",
    [Order.Status.PLACED, Order.Status.SHIPPED, Order.Status.CANCELLED],
)
def test_undelivered_orders_cannot_create(
    client, customer, product, delivered_order, status
):
    delivered_order(customer, product, status=status)
    client.force_login(customer)

    response = post_review(client, product)

    assert_inline_alert(response, HTTPStatus.FORBIDDEN)
    assert not Review.objects.exists()


def test_next_of_kin_cannot_create(
    client, customer, named_customer, product, delivered_order
):
    delivered_order(named_customer, product)
    client.force_login(customer)

    response = post_review(client, product)

    assert_inline_alert(response, HTTPStatus.FORBIDDEN)
    assert not Review.objects.exists()


def test_staff_without_a_purchase_cannot_create(client, staff_user, product):
    client.force_login(staff_user)

    response = post_review(client, product)

    assert_inline_alert(response, HTTPStatus.FORBIDDEN)
    assert not Review.objects.exists()


def test_a_second_review_is_403_and_keeps_the_first(
    client, customer, product, delivered_order, make_review
):
    delivered_order(customer, product)
    make_review(customer, product, comment="The original words.")
    client.force_login(customer)

    response = post_review(client, product, comment="Trying to post twice.")

    html = assert_inline_alert(response, HTTPStatus.FORBIDDEN)
    assert "already reviewed" in html
    assert Review.objects.get().comment == "The original words."


def test_create_for_a_missing_product_is_404_with_an_alert(client, customer):
    client.force_login(customer)

    response = client.post(
        reverse("reviews:create", kwargs={"pk": 999999}), VALID, headers=HTMX
    )

    html = assert_inline_alert(response, HTTPStatus.NOT_FOUND)
    assert "no longer available" in html
    assert not Review.objects.exists()


# --- The duplicate race -------------------------------------------------------


def test_a_duplicate_caught_by_the_database_returns_the_existing_review(
    client, customer, product, delivered_order, make_review, monkeypatch
):
    delivered_order(customer, product)
    existing = make_review(customer, product, comment="Posted from the first tab.")
    # The second tab passed its eligibility check before the first tab's
    # save landed, so only the unique constraint stands in the way.
    monkeypatch.setattr(Review.objects, "eligibility", lambda user, product: "eligible")
    client.force_login(customer)

    response = post_review(client, product, comment="Posted from the second tab.")

    assert response.status_code == HTTPStatus.OK
    assert Review.objects.count() == 1
    assert Review.objects.get().comment == "Posted from the first tab."
    html = response.content.decode()
    assert f'id="review-{existing.pk}"' in html
    assert "Posted from the first tab." in html
    assert "You've already reviewed this product" in html


# --- Signed-out requests ------------------------------------------------------


def test_anonymous_htmx_create_gets_hx_redirect_to_sign_in(client, product):
    response = post_review(client, product)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response["HX-Redirect"] == login_with_next(product)
    assert not Review.objects.exists()


def test_anonymous_plain_create_gets_the_normal_login_redirect(client, product):
    response = client.post(create_url(product), VALID)

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == login_with_next(product)
    assert "HX-Redirect" not in response
    assert not Review.objects.exists()
