"""Discount coupons: percentage-off codes, order-wide or product-limited.

A coupon's terms (code, percent, products) are fixed once created; only
its expiry can change, and retiring is permanent. Orders snapshot what a
coupon gave them, so nothing done to a coupon rewrites order history.
"""

from decimal import ROUND_HALF_UP, Decimal
from functools import cached_property

from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator,
)
from django.db import models
from django.utils import timezone
from django.utils.dateformat import format as format_date

from products.models import Product

CENT = Decimal("0.01")
ZERO = Decimal("0.00")

code_validator = RegexValidator(
    r"^[A-Z0-9]{3,20}$", "Use 3–20 letters and digits, no spaces or symbols."
)


class CouponError(ValueError):
    """A code that can't be used, carrying the reason as a readable message.

    Subclasses ``ValueError`` so ``place_order``'s existing contract — it
    raises ``ValueError`` for anything that stops an order — still holds.
    """


def normalize_code(code: str) -> str:
    """The canonical form of a typed code: no whitespace, uppercase."""
    return "".join(code.split()).upper()


class CouponQuerySet(models.QuerySet):
    def live(self):
        """Coupons that haven't been retired (expired ones included)."""
        return self.filter(retired_at__isnull=True)

    def with_times_used(self):
        return self.annotate(times_used=models.Count("orders"))

    def redeem(self, code: str) -> "Coupon":
        """Return the coupon a customer typed, or raise ``CouponError``.

        Matching ignores case and whitespace. The error message is ready
        to show the customer: not found, expired, or no longer available.
        """
        normalized = normalize_code(code)
        if not normalized:
            raise CouponError("Enter a discount code.")
        try:
            coupon = self.get(code=normalized)
        except self.model.DoesNotExist:
            raise CouponError(f"“{normalized}” isn't a valid discount code.") from None
        coupon.check_redeemable()
        return coupon


class Coupon(models.Model):
    code = models.CharField(max_length=20, unique=True, validators=[code_validator])
    percent_off = models.PositiveSmallIntegerField(
        "percent off",
        validators=[MinValueValidator(1), MaxValueValidator(90)],
        help_text="A whole number from 1 to 90.",
    )
    products = models.ManyToManyField(
        Product,
        blank=True,
        related_name="coupons",
        help_text="Leave empty to apply to the whole order.",
    )
    expires_on = models.DateField(
        "expires on",
        null=True,
        blank=True,
        help_text="Valid through the end of this day. Leave empty to never expire.",
    )
    retired_at = models.DateTimeField(null=True, blank=True, editable=False)
    created_at = models.DateTimeField(default=timezone.now, editable=False)

    objects = CouponQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(percent_off__gte=1, percent_off__lte=90),
                name="coupon_percent_off_1_to_90",
            )
        ]

    def __str__(self):
        return self.code

    def save(self, *args, **kwargs):
        self.code = normalize_code(self.code)
        super().save(*args, **kwargs)

    # --- State ---------------------------------------------------------------

    @property
    def is_retired(self):
        return self.retired_at is not None

    def is_expired(self, today=None):
        """Expired once the store's local date passes ``expires_on``."""
        today = today or timezone.localdate()
        return self.expires_on is not None and today > self.expires_on

    @property
    def status(self):
        """``"Retired"``, ``"Expired"``, or ``"Live"`` — for display."""
        if self.is_retired:
            return "Retired"
        if self.is_expired():
            return "Expired"
        return "Live"

    def check_redeemable(self, today=None):
        """Raise ``CouponError`` with the readable reason if unusable today."""
        if self.is_retired:
            raise CouponError(f"{self.code} is no longer available.")
        if self.is_expired(today):
            raise CouponError(
                f"{self.code} expired on {format_date(self.expires_on, 'F j, Y')}."
            )

    def retire(self):
        """Switch the coupon off for good. Orders that used it are untouched."""
        if not self.is_retired:
            self.retired_at = timezone.now()
            self.save(update_fields=["retired_at"])

    # --- Pricing -------------------------------------------------------------

    @cached_property
    def _product_ids(self):
        return set(self.products.values_list("pk", flat=True))

    @property
    def is_order_wide(self):
        return not self._product_ids

    def applies_to(self, product: Product) -> bool:
        """An order-wide coupon applies to everything; otherwise, its list."""
        return self.is_order_wide or product.pk in self._product_ids

    def discount_for(self, product: Product, amount: Decimal) -> Decimal:
        """The discount on ``amount`` spent on ``product``, rounded half-up
        to the cent — zero if the coupon doesn't cover the product."""
        if not self.applies_to(product):
            return ZERO
        return (amount * self.percent_off / 100).quantize(CENT, ROUND_HALF_UP)
