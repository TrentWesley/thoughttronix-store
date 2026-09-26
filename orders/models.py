from dataclasses import dataclass
from decimal import Decimal

from django.conf import settings
from django.db import models
from django.utils import timezone

from coupons.models import ZERO, Coupon, CouponError
from products.models import Product


class Cart(models.Model):
    """A customer's cart — one per user, created lazily on first touch."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="cart",
    )

    def __str__(self):
        return f"Cart for {self.user.username}"

    @classmethod
    def for_user(cls, user):
        """Return the user's cart, creating it on first touch."""
        cart, _ = cls.objects.get_or_create(user=user)
        return cart

    def add(self, product):
        """Add a product to the cart; a duplicate add increments its line."""
        item, created = self.items.get_or_create(product=product)
        if not created:
            item.quantity += 1
            item.save()
        return item

    def lines(self):
        """Line items with their products loaded, ready for display."""
        return self.items.select_related("product")

    def total(self):
        return sum((item.line_total for item in self.lines()), Decimal("0.00"))

    def priced(self, coupon: Coupon | None = None) -> "PricedCart":
        """The cart's lines and totals with ``coupon`` applied.

        The single pricing path: the checkout page, the coupon preview,
        and ``place_order`` all price through here, so what the customer
        sees is what they're charged. Raises ``CouponError`` if a coupon
        is given but discounts nothing — an order with a coupon always
        got a discount.
        """
        lines = [
            PricedLine(
                item=item,
                discount=(
                    coupon.discount_for(item.product, item.line_total)
                    if coupon
                    else ZERO
                ),
            )
            for item in self.lines()
        ]
        priced = PricedCart(lines=lines, coupon=coupon)
        if coupon is not None and not priced.discount:
            raise CouponError(f"{coupon.code} doesn't apply to anything in your cart.")
        return priced

    def item_count(self):
        """Total units across all lines — the navbar badge number."""
        return self.items.aggregate(count=models.Sum("quantity"))["count"] or 0


class CartItem(models.Model):
    """One product line in a cart; the cart–product pair is unique."""

    cart = models.ForeignKey(Cart, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["cart", "product"], name="unique_cart_product"
            )
        ]

    def __str__(self):
        return f"{self.quantity} × {self.product.name}"

    @property
    def line_total(self):
        return self.product.price * self.quantity

    def increment(self):
        self.quantity += 1
        self.save()

    def decrement(self):
        """Step the quantity down, stopping at one — removal is explicit."""
        if self.quantity > 1:
            self.quantity -= 1
            self.save()


@dataclass(frozen=True)
class PricedLine:
    """A cart line with its share of a coupon's discount."""

    item: CartItem
    discount: Decimal

    @property
    def product(self):
        return self.item.product

    @property
    def quantity(self):
        return self.item.quantity

    @property
    def line_total(self):
        return self.item.line_total

    @property
    def net_total(self):
        return self.line_total - self.discount


@dataclass(frozen=True)
class PricedCart:
    """A priced cart: lines, subtotal, discount, and what will be charged."""

    lines: list[PricedLine]
    coupon: Coupon | None = None

    @property
    def subtotal(self):
        return sum((line.line_total for line in self.lines), ZERO)

    @property
    def discount(self):
        return sum((line.discount for line in self.lines), ZERO)

    @property
    def total(self):
        return self.subtotal - self.discount


class Order(models.Model):
    """A placed order — a snapshot, never a live view of the catalog.

    Addresses are flat denormalized fields: the order must not change if
    the customer later edits anything. Of the card, only the last four
    digits survive checkout. A coupon is snapshotted too — its code and
    the discount it gave — so ``total == subtotal - discount`` holds no
    matter what later happens to the coupon.
    """

    class Status(models.TextChoices):
        PLACED = "PLACED", "Placed"
        SHIPPED = "SHIPPED", "Shipped"
        DELIVERED = "DELIVERED", "Delivered"
        CANCELLED = "CANCELLED", "Cancelled"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="orders",
    )
    status = models.CharField(
        max_length=10, choices=Status.choices, default=Status.PLACED
    )
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    coupon = models.ForeignKey(
        Coupon,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="orders",
    )
    coupon_code = models.CharField(max_length=20, blank=True)
    email = models.EmailField()

    shipping_name = models.CharField(max_length=100)
    shipping_street = models.CharField(max_length=200)
    shipping_line2 = models.CharField(max_length=200, blank=True)
    shipping_city = models.CharField(max_length=100)
    shipping_state = models.CharField(max_length=2)
    shipping_zip = models.CharField(max_length=10)

    billing_name = models.CharField(max_length=100)
    billing_street = models.CharField(max_length=200)
    billing_line2 = models.CharField(max_length=200, blank=True)
    billing_city = models.CharField(max_length=100)
    billing_state = models.CharField(max_length=2)
    billing_zip = models.CharField(max_length=10)

    card_last4 = models.CharField(max_length=4)

    # default (not auto_now_add) so the seed can backdate orders.
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.number

    @property
    def number(self):
        """The customer-facing order number, e.g. ``TT-2026-00042``."""
        return f"TT-{self.created_at.year}-{self.pk:05d}"


class OrderItem(models.Model):
    """One line of an order, priced as of purchase time.

    Name, unit price, and coupon discount are denormalized: order history
    must not change when the catalog or a coupon does. The product FK survives for linking while the
    product exists.
    """

    order = models.ForeignKey(Order, on_delete=models.CASCADE, related_name="items")
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    product_name = models.CharField(max_length=200)
    unit_price = models.DecimalField(max_digits=10, decimal_places=2)
    quantity = models.PositiveIntegerField()
    discount = models.DecimalField(max_digits=10, decimal_places=2, default=ZERO)

    class Meta:
        ordering = ["pk"]

    def __str__(self):
        return f"{self.quantity} × {self.product_name}"

    @property
    def line_total(self):
        """Before any coupon discount."""
        return self.unit_price * self.quantity

    @property
    def net_total(self):
        """What was actually charged for the line."""
        return self.line_total - self.discount
