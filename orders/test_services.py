"""place_order tests — coverage priority 3 in the PRD.

Denormalization, cart emptying, atomicity, unavailable rejection, the
card_last4-only rule, and coupon redemption with its snapshot.
"""

from decimal import Decimal

import pytest

from coupons.models import CouponError
from products.models import Product

from .models import CartItem, Order, OrderItem
from .services import place_order
from .test_checkout_form import VALID_DATA


@pytest.fixture
def checkout_data():
    return dict(VALID_DATA)


def test_creates_an_order_with_denormalized_snapshot(cart, cart_item, checkout_data):
    order = place_order(cart, cart.user, checkout_data)

    assert order.user == cart.user
    assert order.total == Decimal("699.98")
    assert order.status == Order.Status.PLACED
    item = order.items.get()
    assert item.product_name == "Seraphine Home Hub"
    assert item.unit_price == Decimal("349.99")
    assert item.quantity == 2
    assert item.line_total == Decimal("699.98")


def test_order_history_survives_catalog_changes(cart, cart_item, checkout_data):
    order = place_order(cart, cart.user, checkout_data)

    product = cart_item.product
    product.name = "Seraphine Home Hub II"
    product.price = Decimal("999.00")
    product.save()

    item = order.items.get()
    assert item.product_name == "Seraphine Home Hub"
    assert item.unit_price == Decimal("349.99")


def test_addresses_and_email_are_copied_onto_the_order(cart, cart_item, checkout_data):
    order = place_order(cart, cart.user, checkout_data)

    assert order.email == "casey@example.com"
    assert order.shipping_street == "12 Cortex Lane"
    assert order.shipping_line2 == "Unit 7"
    assert order.shipping_state == "TX"
    assert order.billing_zip == "79015-1234"


def test_only_the_last_four_card_digits_are_stored(cart, cart_item, checkout_data):
    order = place_order(cart, cart.user, checkout_data)

    assert order.card_last4 == "4242"
    stored = [field.name for field in Order._meta.get_fields()]
    assert "card_number" not in stored
    assert "card_cvv" not in stored
    assert "card_expiry" not in stored


def test_the_cart_is_emptied(cart, cart_item, checkout_data):
    place_order(cart, cart.user, checkout_data)

    assert not cart.items.exists()
    assert cart.total() == Decimal("0.00")


def test_an_empty_cart_is_rejected(cart, checkout_data):
    with pytest.raises(ValueError):
        place_order(cart, cart.user, checkout_data)

    assert not Order.objects.exists()


def test_an_unavailable_product_is_rejected(
    cart, cart_item, unavailable_product, checkout_data
):
    cart.items.create(product=unavailable_product)

    with pytest.raises(ValueError, match="EchoPatch"):
        place_order(cart, cart.user, checkout_data)

    assert not Order.objects.exists()
    assert cart.items.count() == 2  # the cart is untouched


def test_a_failure_midway_leaves_no_partial_order(
    cart, cart_item, category, checkout_data, monkeypatch
):
    """All-or-nothing: if any line fails, no order and no emptied cart."""
    cart.add(
        Product.objects.create(
            name="Charging Pillow",
            slug="charging-pillow",
            price=Decimal("69.00"),
            category=category,
        )
    )

    original = OrderItem.objects.create
    calls = {"count": 0}

    def create_then_explode(**kwargs):
        calls["count"] += 1
        if calls["count"] == 2:
            raise RuntimeError("boom")
        return original(**kwargs)

    monkeypatch.setattr(OrderItem.objects, "create", create_then_explode)

    with pytest.raises(RuntimeError):
        place_order(cart, cart.user, checkout_data)

    assert not Order.objects.exists()
    assert not OrderItem.objects.exists()
    assert CartItem.objects.count() == 2


# --- Coupons -----------------------------------------------------------------


def test_without_a_coupon_the_subtotal_is_the_total(cart, cart_item, checkout_data):
    order = place_order(cart, cart.user, checkout_data)

    assert order.subtotal == order.total == Decimal("699.98")
    assert order.discount == Decimal("0.00")
    assert order.coupon is None
    assert order.coupon_code == ""


def test_an_order_wide_coupon_discounts_every_line(
    cart, cart_item, other_product, coupon, checkout_data
):
    cart.add(other_product)  # 69.00

    order = place_order(cart, cart.user, checkout_data, coupon_code="thoughts10")

    assert order.subtotal == Decimal("768.98")
    assert order.discount == Decimal("76.90")  # 70.00 + 6.90
    assert order.total == Decimal("692.08")
    assert order.coupon == coupon
    assert order.coupon_code == "THOUGHTS10"
    assert [item.discount for item in order.items.all()] == [
        Decimal("70.00"),
        Decimal("6.90"),
    ]


def test_a_product_limited_coupon_discounts_only_its_lines(
    cart, cart_item, other_product, product_coupon, checkout_data
):
    cart.add(other_product)

    order = place_order(cart, cart.user, checkout_data, coupon_code="HUB20")

    hub, pillow = order.items.all()
    assert hub.discount == Decimal("140.00")  # 20% of 699.98, rounded half-up
    assert pillow.discount == Decimal("0.00")
    assert order.discount == hub.discount
    assert order.total == order.subtotal - order.discount == Decimal("628.98")


def test_a_coupon_matching_nothing_in_the_cart_is_rejected(
    cart, other_product, product_coupon, checkout_data
):
    cart.add(other_product)

    with pytest.raises(CouponError, match="HUB20 doesn't apply to anything"):
        place_order(cart, cart.user, checkout_data, coupon_code="HUB20")

    assert not Order.objects.exists()
    assert cart.items.exists()


def test_a_retired_coupon_is_rejected_and_the_cart_kept(
    cart, cart_item, coupon, checkout_data
):
    coupon.retire()

    with pytest.raises(ValueError, match="no longer available"):
        place_order(cart, cart.user, checkout_data, coupon_code="THOUGHTS10")

    assert not Order.objects.exists()
    assert cart.items.exists()


def test_an_unknown_coupon_is_rejected(cart, cart_item, checkout_data):
    with pytest.raises(CouponError, match="isn't a valid discount code"):
        place_order(cart, cart.user, checkout_data, coupon_code="NOPE")

    assert not Order.objects.exists()


def test_the_snapshot_survives_retiring_the_coupon(
    cart, cart_item, coupon, checkout_data
):
    order = place_order(cart, cart.user, checkout_data, coupon_code="THOUGHTS10")

    coupon.retire()

    order.refresh_from_db()
    assert order.coupon_code == "THOUGHTS10"
    assert order.discount == Decimal("70.00")
    assert order.total == Decimal("629.98")
    assert order.items.get().discount == Decimal("70.00")
