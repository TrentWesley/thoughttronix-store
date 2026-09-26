"""Coupons at checkout: cart pricing, the HTMX preview, placing the order,
and the discount shown wherever an order's money is."""

import datetime
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.urls import reverse

from coupons.models import CouponError

from .models import Cart, CartItem, Order
from .services import place_order
from .test_checkout_form import VALID_DATA

pytestmark = pytest.mark.django_db


# --- Cart.priced -------------------------------------------------------------


def test_priced_without_a_coupon_matches_the_cart_total(cart, cart_item):
    priced = cart.priced()

    assert priced.subtotal == priced.total == cart.total() == Decimal("699.98")
    assert priced.discount == Decimal("0.00")
    assert priced.coupon is None


def test_priced_with_a_coupon_splits_the_discount_by_line(
    cart, cart_item, other_product, product_coupon
):
    cart.add(other_product)

    priced = cart.priced(product_coupon)

    assert [line.discount for line in priced.lines] == [
        Decimal("140.00"),
        Decimal("0.00"),
    ]
    assert priced.lines[0].net_total == Decimal("559.98")
    assert priced.total == Decimal("628.98")


def test_priced_rejects_a_coupon_that_discounts_nothing(
    cart, other_product, product_coupon
):
    cart.add(other_product)

    with pytest.raises(CouponError, match="doesn't apply to anything in your cart"):
        cart.priced(product_coupon)


# --- The HTMX preview --------------------------------------------------------


def preview(client, code):
    return client.post(reverse("orders:coupon_preview"), {"coupon_code": code})


def test_preview_requires_login(client, db):
    response = preview(client, "THOUGHTS10")

    assert response.status_code == HTTPStatus.FOUND
    assert reverse("accounts:login") in response.url


def test_preview_shows_the_discounted_summary(client, customer, cart_item, coupon):
    client.force_login(customer)

    response = preview(client, "thoughts10")

    page = response.content.decode()
    assert response.status_code == HTTPStatus.OK
    assert "<html" not in page  # a partial, never base.html
    assert "THOUGHTS10</span> applied" in page
    assert "−$70.00" in page
    assert 'id="place-order-total" hx-swap-oob="true">$629.98' in page


def test_preview_shows_the_readable_reason_for_a_bad_code(
    client, customer, cart_item, coupon
):
    coupon.retire()
    client.force_login(customer)

    response = preview(client, "THOUGHTS10")

    page = response.content.decode()
    assert "THOUGHTS10 is no longer available." in page
    assert "$699.98" in page  # priced without it


def test_preview_explains_a_coupon_that_matches_nothing(
    client, customer, other_product, product_coupon
):
    Cart.for_user(customer).add(other_product)
    client.force_login(customer)

    response = preview(client, "HUB20")

    assert "HUB20 doesn&#x27;t apply to anything in your cart." in (
        response.content.decode()
    )


def test_preview_stores_nothing(client, customer, cart_item, coupon):
    client.force_login(customer)
    preview(client, "THOUGHTS10")

    response = client.get(reverse("orders:checkout"))

    assert "applied" not in response.content.decode()
    assert response.context["priced"].coupon is None


# --- Placing the order -------------------------------------------------------


def test_the_checkout_page_has_the_coupon_field(client, customer, cart_item):
    client.force_login(customer)

    page = client.get(reverse("orders:checkout")).content.decode()

    assert 'name="coupon_code"' in page
    assert reverse("orders:coupon_preview") in page


def test_checkout_with_a_coupon_places_a_discounted_order(
    client, customer, cart_item, coupon
):
    client.force_login(customer)

    response = client.post(
        reverse("orders:checkout"), {**VALID_DATA, "coupon_code": "thoughts10"}
    )

    order = Order.objects.get()
    assert response.status_code == HTTPStatus.FOUND
    assert order.coupon_code == "THOUGHTS10"
    assert order.total == Decimal("629.98")


def test_an_expired_code_blocks_the_order_with_its_reason(
    client, customer, cart_item, coupon
):
    coupon.expires_on = datetime.date(2020, 3, 5)
    coupon.save()
    client.force_login(customer)

    response = client.post(
        reverse("orders:checkout"), {**VALID_DATA, "coupon_code": "THOUGHTS10"}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["coupon_code"] == [
        "THOUGHTS10 expired on March 5, 2020."
    ]
    assert "12 Cortex Lane" in response.content.decode()  # input preserved
    assert not Order.objects.exists()
    assert CartItem.objects.exists()


def test_a_coupon_matching_nothing_blocks_the_order_on_the_field(
    client, customer, other_product, product_coupon
):
    """The one rule the form can't check: it surfaces from place_order."""
    Cart.for_user(customer).add(other_product)
    client.force_login(customer)

    response = client.post(
        reverse("orders:checkout"), {**VALID_DATA, "coupon_code": "HUB20"}
    )

    assert response.status_code == HTTPStatus.OK
    assert response.context["form"].errors["coupon_code"] == [
        "HUB20 doesn't apply to anything in your cart."
    ]
    assert not Order.objects.exists()


# --- Showing the discount ----------------------------------------------------


@pytest.fixture
def discounted_order(cart, cart_item, coupon):
    return place_order(cart, cart.user, dict(VALID_DATA), coupon_code="THOUGHTS10")


def test_customer_pages_show_the_discount(client, customer, discounted_order):
    client.force_login(customer)

    for name in ["orders:confirmation", "orders:detail"]:
        page = client.get(
            reverse(name, kwargs={"pk": discounted_order.pk})
        ).content.decode()

        assert "Subtotal" in page, name
        assert "(THOUGHTS10)" in page, name
        assert "−$70.00" in page, name
        assert "$629.98" in page, name


def test_back_office_order_detail_shows_the_discount(
    client, staff_user, discounted_order
):
    client.force_login(staff_user)

    page = client.get(
        reverse("orders:manage_order_detail", kwargs={"pk": discounted_order.pk})
    ).content.decode()

    assert "−$70.00 with THOUGHTS10" in page
    assert "(THOUGHTS10)" in page


def test_an_order_without_a_coupon_shows_no_discount_lines(
    client, customer, cart, cart_item
):
    order = place_order(cart, cart.user, dict(VALID_DATA))
    client.force_login(customer)

    page = client.get(reverse("orders:detail", kwargs={"pk": order.pk})).content
    page = page.decode()

    assert "Subtotal" not in page
    assert "Discount" not in page
    assert "$699.98" in page
