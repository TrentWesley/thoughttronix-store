"""Coupon model behavior: codes, state, redemption messages, and the math."""

import datetime
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from .models import Coupon, CouponError, normalize_code
from .validators import validate_coupon_code

pytestmark = pytest.mark.django_db

TODAY = datetime.date(2026, 9, 30)


# --- Codes -------------------------------------------------------------------


def test_normalize_code_strips_whitespace_and_uppercases():
    assert normalize_code("  thoughts 10\t") == "THOUGHTS10"


def test_codes_are_saved_in_canonical_form():
    coupon = Coupon.objects.create(code="thoughts10", percent_off=10)

    assert coupon.code == "THOUGHTS10"


def test_codes_are_unique_regardless_of_case(coupon):
    with pytest.raises(IntegrityError):
        Coupon.objects.create(code="Thoughts10", percent_off=20)


@pytest.mark.parametrize("code", ["AB", "A" * 21, "SAVE-10", "SAVE_10"])
def test_malformed_codes_fail_validation(code):
    with pytest.raises(ValidationError) as excinfo:
        Coupon(code=code, percent_off=10).full_clean()

    assert "code" in excinfo.value.message_dict


@pytest.mark.parametrize("percent", [0, 91])
def test_percent_off_is_capped_between_1_and_90(percent):
    with pytest.raises(ValidationError) as excinfo:
        Coupon(code="EDGE", percent_off=percent).full_clean()

    assert "percent_off" in excinfo.value.message_dict


def test_the_database_enforces_the_percent_cap_too():
    with pytest.raises(IntegrityError):
        Coupon.objects.create(code="GREEDY", percent_off=95)


# --- State and redemption ----------------------------------------------------


def test_redeem_matches_any_case_and_spacing(coupon):
    assert Coupon.objects.redeem(" thoughts10 ") == coupon


def test_an_unknown_code_is_rejected_readably(db):
    with pytest.raises(CouponError, match="“NOPE” isn't a valid discount code."):
        Coupon.objects.redeem("nope")


def test_a_blank_code_is_rejected(db):
    with pytest.raises(CouponError, match="Enter a discount code."):
        Coupon.objects.redeem("   ")


def test_a_coupon_is_valid_through_its_expiry_day(coupon):
    coupon.expires_on = TODAY
    coupon.save()

    coupon.check_redeemable(today=TODAY)  # no error on the last day
    with pytest.raises(CouponError, match="THOUGHTS10 expired on September 30, 2026."):
        coupon.check_redeemable(today=TODAY + datetime.timedelta(days=1))


def test_redeem_rejects_an_expired_coupon(coupon):
    coupon.expires_on = timezone.localdate() - datetime.timedelta(days=1)
    coupon.save()

    with pytest.raises(CouponError, match="expired on"):
        Coupon.objects.redeem("THOUGHTS10")


def test_redeem_rejects_a_retired_coupon(coupon):
    coupon.retire()

    with pytest.raises(CouponError, match="THOUGHTS10 is no longer available."):
        Coupon.objects.redeem("THOUGHTS10")


def test_retiring_is_recorded_once(coupon):
    coupon.retire()
    first = coupon.retired_at
    coupon.retire()

    coupon.refresh_from_db()
    assert coupon.retired_at == first
    assert coupon.is_retired


def test_status_for_display(coupon):
    assert coupon.status == "Live"
    coupon.expires_on = timezone.localdate() - datetime.timedelta(days=1)
    assert coupon.status == "Expired"
    coupon.retire()
    assert coupon.status == "Retired"


def test_live_excludes_retired_coupons(coupon, product_coupon):
    product_coupon.retire()

    assert list(Coupon.objects.live()) == [coupon]


def test_the_checkout_validator_carries_the_coupons_reason(coupon):
    coupon.retire()

    with pytest.raises(ValidationError) as excinfo:
        validate_coupon_code("thoughts10")

    assert excinfo.value.messages == ["THOUGHTS10 is no longer available."]


# --- Scope and the math ------------------------------------------------------


def test_an_empty_product_list_means_order_wide(coupon, product, other_product):
    assert coupon.is_order_wide
    assert coupon.applies_to(product)
    assert coupon.applies_to(other_product)


def test_a_product_limited_coupon_covers_only_its_products(
    product_coupon, product, other_product
):
    assert not product_coupon.is_order_wide
    assert product_coupon.applies_to(product)
    assert not product_coupon.applies_to(other_product)


def test_discount_is_the_percentage_rounded_half_up(coupon, product):
    # 10% of 0.05 is 0.005 — half a cent rounds up.
    assert coupon.discount_for(product, Decimal("0.05")) == Decimal("0.01")
    assert coupon.discount_for(product, Decimal("699.98")) == Decimal("70.00")


def test_discount_is_zero_off_scope(product_coupon, other_product):
    assert product_coupon.discount_for(other_product, Decimal("69.00")) == Decimal(
        "0.00"
    )
