"""The checkout's coupon-code validator.

Unlike checkout's pure card validators, this one reads the database: a
code is only valid if a live, unexpired coupon carries it. Whether the
coupon covers anything in the cart is checked later, by pricing the
cart — the form doesn't know the cart.
"""

from django.core.exceptions import ValidationError

from .models import Coupon, CouponError


def validate_coupon_code(value: str) -> None:
    """Reject a code that doesn't redeem, with the coupon's own reason."""
    try:
        Coupon.objects.redeem(value)
    except CouponError as error:
        raise ValidationError(str(error), code="coupon_code") from error
