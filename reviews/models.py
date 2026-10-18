"""Product reviews: one star rating and comment per customer per product.

Every rule about reviews lives here, in ``Review`` and its queryset.
"""

from dataclasses import dataclass

from django.conf import settings
from django.core.validators import MaxLengthValidator, MinLengthValidator
from django.db import models
from django.utils import timezone

from products.models import Product

COMMENT_MIN_LENGTH = 10
COMMENT_MAX_LENGTH = 2000


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
