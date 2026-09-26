"""Back-office coupon management: access, create, edit expiry, retire."""

import datetime
from decimal import Decimal
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from orders.services import place_order
from orders.test_checkout_form import VALID_DATA

from .models import Coupon

pytestmark = pytest.mark.django_db


def manage_urls(coupon):
    return [
        reverse("coupons:manage_coupons"),
        reverse("coupons:manage_coupon_create"),
        reverse("coupons:manage_coupon_update", kwargs={"pk": coupon.pk}),
        reverse("coupons:manage_coupon_retire", kwargs={"pk": coupon.pk}),
    ]


def in_days(days):
    return (timezone.localdate() + datetime.timedelta(days=days)).isoformat()


# --- Access control ----------------------------------------------------------


def test_anonymous_users_are_sent_to_login(client, coupon):
    for url in manage_urls(coupon):
        response = client.get(url)

        assert response.status_code == HTTPStatus.FOUND, url
        assert reverse("accounts:login") in response.url


def test_customers_are_forbidden(client, customer, coupon):
    client.force_login(customer)

    for url in manage_urls(coupon):
        assert client.get(url).status_code == HTTPStatus.FORBIDDEN, url


def test_staff_can_reach_every_page(client, staff_user, coupon):
    client.force_login(staff_user)

    for url in manage_urls(coupon):
        assert client.get(url).status_code == HTTPStatus.OK, url


# --- The list ----------------------------------------------------------------


def test_list_has_a_designed_empty_state(client, staff_user):
    client.force_login(staff_user)

    response = client.get(reverse("coupons:manage_coupons"))

    assert "No coupons yet" in response.content.decode()


def test_list_shows_scope_status_and_times_used(
    client, staff_user, coupon, product_coupon, cart, cart_item
):
    place_order(cart, cart.user, dict(VALID_DATA), coupon_code="THOUGHTS10")
    product_coupon.retire()
    client.force_login(staff_user)

    response = client.get(reverse("coupons:manage_coupons"))

    listed = {c.code: c for c in response.context["coupons"]}
    assert listed["THOUGHTS10"].times_used == 1
    assert listed["HUB20"].times_used == 0
    page = response.content.decode()
    assert "Order-wide" in page
    assert "Seraphine Home Hub" in page
    assert "Retired" in page


# --- Create ------------------------------------------------------------------


def test_staff_can_create_a_product_limited_coupon(client, staff_user, product):
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_create"),
        {
            "code": " spring 15 ",
            "percent_off": "15",
            "products": [str(product.pk)],
            "expires_on": in_days(30),
        },
    )

    assert response.status_code == HTTPStatus.FOUND
    coupon = Coupon.objects.get()
    assert coupon.code == "SPRING15"
    assert list(coupon.products.all()) == [product]


def test_a_duplicate_code_is_rejected_whatever_its_case(client, staff_user, coupon):
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_create"),
        {"code": "thoughts10", "percent_off": "20"},
    )

    assert response.status_code == HTTPStatus.OK
    assert "code" in response.context["form"].errors
    assert Coupon.objects.count() == 1


def test_a_retired_code_can_never_be_reused(client, staff_user, coupon):
    coupon.retire()
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_create"),
        {"code": "THOUGHTS10", "percent_off": "20"},
    )

    assert "code" in response.context["form"].errors


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("code", "NO-SYMBOLS"),
        ("percent_off", "0"),
        ("percent_off", "91"),
        ("expires_on", "2020-01-01"),
    ],
)
def test_bad_coupon_input_is_rejected(client, staff_user, field, value):
    client.force_login(staff_user)
    data = {"code": "GOOD10", "percent_off": "10", field: value}

    response = client.post(reverse("coupons:manage_coupon_create"), data)

    assert field in response.context["form"].errors
    assert not Coupon.objects.exists()


# --- Edit expiry -------------------------------------------------------------


def test_only_the_expiry_can_be_edited(client, staff_user, product_coupon):
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_update", kwargs={"pk": product_coupon.pk}),
        {"expires_on": in_days(10), "code": "HACKED", "percent_off": "90"},
    )

    assert response.status_code == HTTPStatus.FOUND
    product_coupon.refresh_from_db()
    assert product_coupon.expires_on.isoformat() == in_days(10)
    assert product_coupon.code == "HUB20"
    assert product_coupon.percent_off == 20


def test_a_retired_coupon_cannot_be_edited_or_retired_again(client, staff_user, coupon):
    coupon.retire()
    client.force_login(staff_user)

    for name in ["coupons:manage_coupon_update", "coupons:manage_coupon_retire"]:
        url = reverse(name, kwargs={"pk": coupon.pk})
        assert client.get(url).status_code == HTTPStatus.NOT_FOUND, name


# --- Retire ------------------------------------------------------------------


def test_retiring_leaves_past_orders_untouched(
    client, staff_user, coupon, cart, cart_item
):
    order = place_order(cart, cart.user, dict(VALID_DATA), coupon_code="THOUGHTS10")
    client.force_login(staff_user)

    response = client.post(
        reverse("coupons:manage_coupon_retire", kwargs={"pk": coupon.pk})
    )

    assert response.status_code == HTTPStatus.FOUND
    coupon.refresh_from_db()
    assert coupon.is_retired
    order.refresh_from_db()
    assert order.coupon == coupon
    assert order.coupon_code == "THOUGHTS10"
    assert order.discount == Decimal("70.00")
    assert order.total == Decimal("629.98")


def test_the_retire_page_only_asks_first(client, staff_user, coupon):
    client.force_login(staff_user)

    response = client.get(
        reverse("coupons:manage_coupon_retire", kwargs={"pk": coupon.pk})
    )

    assert "Retire" in response.content.decode()
    coupon.refresh_from_db()
    assert not coupon.is_retired
