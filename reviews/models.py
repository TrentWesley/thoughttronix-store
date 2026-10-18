"""Product reviews: one star rating and comment per customer per product.

Every rule about reviews lives here, in ``Review`` and its queryset.
"""

from dataclasses import dataclass

from django.conf import settings
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.utils import timezone

from orders.models import Order
from products.models import Product

COMMENT_MIN_LENGTH = 10
COMMENT_MAX_LENGTH = 2000


class Eligibility(models.TextChoices):
    """Whether a user may write a review of a product, and if not, why."""

    ELIGIBLE = "eligible", "Eligible"
    SIGNED_OUT = "signed_out", "Signed out"
    NOT_PURCHASED = "not_purchased", "No delivered purchase"
    ALREADY_REVIEWED = "already_reviewed", "Already reviewed"


@dataclass(frozen=True)
class ReviewSummary:
    """A product's live review summary: average rating and review count."""

    average: float | None
    count: int

    @property
    def stars(self) -> int:
        """The average rounded half up to whole stars, 0 with no reviews."""
        if self.average is None:
            return 0
        return int(self.average + 0.5)


class ReviewQuerySet(models.QuerySet):
    def newest_first(self):
        """Reviews newest first, with their authors loaded for display."""
        return self.select_related("user").order_by("-created_at", "-pk")

    def excluding(self, *reviews):
        """Leave out the given (pinned) reviews; ``None`` entries are skipped."""
        return self.exclude(pk__in=[review.pk for review in reviews if review])

    def editable_by(self, user):
        """The reviews ``user`` may edit or delete: staff any, others their own.

        Authorship alone decides — not eligibility — so a review stays the
        author's to change after its order is cancelled.
        """
        if user.is_staff:
            return self
        return self.filter(user=user)

    def eligibility(self, user, product) -> Eligibility:
        """May ``user`` write a review of ``product``? If not, why not.

        Only the user's own delivered orders and reviews count: product
        availability is ignored and staff get no exemption. Checked at
        creation only — an existing review outlives its order.
        """
        if not user.is_authenticated:
            return Eligibility.SIGNED_OUT
        if self.filter(user=user, product=product).exists():
            return Eligibility.ALREADY_REVIEWED
        if not Order.objects.filter(user=user).delivered_containing(product).exists():
            return Eligibility.NOT_PURCHASED
        return Eligibility.ELIGIBLE

    def summary(self) -> ReviewSummary:
        """The average rating and count, in one aggregate query."""
        result = self.aggregate(average=models.Avg("rating"), count=models.Count("pk"))
        return ReviewSummary(average=result["average"], count=result["count"])


class Review(models.Model):
    class Rating(models.IntegerChoices):
        ONE = 1, "1 star"
        TWO = 2, "2 stars"
        THREE = 3, "3 stars"
        FOUR = 4, "4 stars"
        FIVE = 5, "5 stars"

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="reviews"
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name="reviews"
    )
    rating = models.PositiveSmallIntegerField(choices=Rating.choices)
    comment = models.TextField(
        validators=[
            MinLengthValidator(COMMENT_MIN_LENGTH),
            MaxLengthValidator(COMMENT_MAX_LENGTH),
        ]
    )
    # default (not auto_now_add) so tests and the seed can backdate reviews.
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)
    # Set on edits; these, not updated_at, drive the "Edited" labels.
    edited_at = models.DateTimeField(null=True, blank=True)
    edited_by_staff_at = models.DateTimeField(null=True, blank=True)

    objects = ReviewQuerySet.as_manager()

    class Meta:
        ordering = ["-created_at", "-pk"]
        constraints = [
            models.UniqueConstraint(
                fields=["user", "product"],
                name="unique_review_user_product",
                violation_error_message="You've already reviewed this product.",
            ),
            models.CheckConstraint(
                condition=models.Q(rating__gte=1, rating__lte=5),
                name="review_rating_1_to_5",
            ),
        ]

    def __str__(self):
        return f"{self.rating}★ {self.product} by {self.user}"

    @property
    def display_name(self) -> str:
        """The reviewer's public name: "Margaret W.", "Margaret", or neither.

        Never a username, email address, or full last name — without a
        first name on file, the reviewer is a "Verified customer".
        """
        first = self.user.first_name.strip()
        last = self.user.last_name.strip()
        if not first:
            return "Verified customer"
        if not last:
            return first
        return f"{first} {last[0]}."

    def record_edit(self, editor) -> None:
        """Mark this review as edited by ``editor`` (unsaved).

        Every edit sets ``edited_at``. An edit by anyone but the author —
        staff, since only they can reach someone else's review — sets
        ``edited_by_staff_at``; the author's own edit clears it, because
        the words are theirs again.
        """
        now = timezone.now()
        self.edited_at = now
        self.edited_by_staff_at = None if editor.pk == self.user_id else now
