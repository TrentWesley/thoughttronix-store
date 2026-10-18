"""Who may write a review: ``Review.objects.eligibility(user, product)``.

Only the reviewer's own delivered order counts. Availability is ignored
and staff get no exemption.
"""

import pytest
from django.contrib.auth.models import AnonymousUser

from orders.models import Order

from .models import Review


def test_a_delivered_order_qualifies(customer, product, delivered_order):
    delivered_order(customer, product)

    assert Review.objects.eligibility(customer, product) == "eligible"


@pytest.mark.parametrize(
    "status",
    [Order.Status.PLACED, Order.Status.SHIPPED, Order.Status.CANCELLED],
)
def test_undelivered_orders_do_not_qualify(customer, product, delivered_order, status):
    delivered_order(customer, product, status=status)

    assert Review.objects.eligibility(customer, product) == "not_purchased"


def test_no_order_at_all_is_refused(customer, product):
    assert Review.objects.eligibility(customer, product) == "not_purchased"


def test_a_delivered_order_for_another_product_does_not_qualify(
    customer, product, other_product, delivered_order
):
    delivered_order(customer, other_product)

    assert Review.objects.eligibility(customer, product) == "not_purchased"


def test_signed_out_is_refused(product):
    assert Review.objects.eligibility(AnonymousUser(), product) == "signed_out"


def test_already_reviewed_is_refused(customer, product, delivered_order, make_review):
    delivered_order(customer, product)
    make_review(customer, product)

    assert Review.objects.eligibility(customer, product) == "already_reviewed"


def test_already_reviewed_wins_even_after_the_order_is_cancelled(
    customer, product, delivered_order, make_review
):
    order = delivered_order(customer, product)
    make_review(customer, product)
    order.status = Order.Status.CANCELLED
    order.save()

    assert Review.objects.eligibility(customer, product) == "already_reviewed"


def test_next_of_kin_is_refused(customer, named_customer, product, delivered_order):
    # Margaret bought and received the product; her relative did not.
    delivered_order(named_customer, product)

    assert Review.objects.eligibility(customer, product) == "not_purchased"


def test_another_users_review_does_not_block_mine(
    customer, named_customer, product, delivered_order, make_review
):
    delivered_order(customer, product)
    make_review(named_customer, product)

    assert Review.objects.eligibility(customer, product) == "eligible"


def test_a_verified_purchaser_can_review_an_unavailable_product(
    customer, unavailable_product, delivered_order
):
    delivered_order(customer, unavailable_product)

    assert Review.objects.eligibility(customer, unavailable_product) == "eligible"


def test_staff_without_a_purchase_are_refused(staff_user, product):
    assert Review.objects.eligibility(staff_user, product) == "not_purchased"


def test_staff_with_a_delivered_order_qualify(staff_user, product, delivered_order):
    delivered_order(staff_user, product)

    assert Review.objects.eligibility(staff_user, product) == "eligible"
