from datetime import timedelta
from decimal import Decimal

import pytest
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.utils import timezone

from orders.models import OrderItem

from .models import Review

# --- Database constraints ----------------------------------------------------


def test_one_review_per_user_per_product(customer, product, make_review):
    make_review(customer, product)

    with pytest.raises(IntegrityError):
        make_review(customer, product)


def test_same_user_may_review_different_products(
    customer, product, other_product, make_review
):
    make_review(customer, product)
    make_review(customer, other_product)

    assert Review.objects.count() == 2


@pytest.mark.parametrize("rating", [0, 6])
def test_database_rejects_out_of_range_ratings(customer, product, rating):
    with pytest.raises(IntegrityError):
        Review.objects.create(
            user=customer, product=product, rating=rating, comment="Out of range."
        )


# --- Model validation --------------------------------------------------------


@pytest.mark.parametrize("length", [9, 2001])
def test_model_validation_rejects_comment_length(customer, product, length):
    review = Review(user=customer, product=product, rating=4, comment="x" * length)

    with pytest.raises(ValidationError) as excinfo:
        review.full_clean()

    assert "comment" in excinfo.value.message_dict


@pytest.mark.parametrize("length", [10, 2000])
def test_model_validation_accepts_comment_length(customer, product, length):
    review = Review(user=customer, product=product, rating=4, comment="x" * length)

    review.full_clean()


@pytest.mark.parametrize("rating", [0, 6])
def test_model_validation_rejects_out_of_range_ratings(customer, product, rating):
    review = Review(user=customer, product=product, rating=rating, comment="x" * 10)

    with pytest.raises(ValidationError) as excinfo:
        review.full_clean()

    assert "rating" in excinfo.value.message_dict


def test_new_review_has_no_edit_timestamps(customer, product, make_review):
    review = make_review(customer, product)

    assert review.edited_at is None
    assert review.edited_by_staff_at is None


# --- Cascades ----------------------------------------------------------------


def test_deleting_a_product_deletes_its_reviews(customer, product, make_review):
    make_review(customer, product)

    product.delete()

    assert not Review.objects.exists()


def test_deleting_a_user_deletes_their_reviews(
    customer, named_customer, product, make_review
):
    make_review(customer, product)
    kept = make_review(named_customer, product)

    customer.delete()

    assert list(Review.objects.all()) == [kept]


def test_order_line_history_survives_a_reviewed_product_deletion(
    customer, product, delivered_order, make_review
):
    order = delivered_order(customer, product)
    make_review(customer, product)

    product.delete()

    line = OrderItem.objects.get(order=order)
    assert line.product is None
    assert line.product_name == "Seraphine Home Hub"
    assert line.unit_price == Decimal("349.99")


# --- Public display name -----------------------------------------------------


def make_user(username, first_name="", last_name=""):
    return get_user_model().objects.create_user(
        username=username,
        password="pw-for-tests-123",
        email=f"{username}@example.com",
        first_name=first_name,
        last_name=last_name,
    )


def test_display_name_with_both_names(named_customer, product, make_review):
    review = make_review(named_customer, product)

    assert review.display_name == "Margaret W."


def test_display_name_with_no_last_name(db, product, make_review):
    review = make_review(make_user("margaret_only", "Margaret"), product)

    assert review.display_name == "Margaret"


@pytest.mark.parametrize("last_name", ["", "Wren"])
def test_display_name_with_no_first_name(db, product, make_review, last_name):
    review = make_review(make_user("anon_buyer", last_name=last_name), product)

    assert review.display_name == "Verified customer"


def test_display_name_ignores_whitespace_only_names(db, product, make_review):
    review = make_review(make_user("spaces", "   ", "   "), product)

    assert review.display_name == "Verified customer"


def test_display_name_never_reveals_username_or_email(
    named_customer, product, make_review
):
    review = make_review(named_customer, product)

    assert "mwren_login" not in review.display_name
    assert "@" not in review.display_name
    assert "Wren" not in review.display_name


# --- Queryset: summary and listing -------------------------------------------


def test_summary_of_no_reviews(product):
    summary = Review.objects.filter(product=product).summary()

    assert summary.count == 0
    assert summary.average is None


def test_summary_average_and_count(
    customer, named_customer, staff_user, product, other_product, make_review
):
    make_review(customer, product, rating=5)
    make_review(named_customer, product, rating=4)
    make_review(staff_user, product, rating=2)
    make_review(customer, other_product, rating=1)

    summary = product.reviews.summary()

    assert summary.count == 3
    assert summary.average == pytest.approx(11 / 3)


@pytest.mark.parametrize(
    ("ratings", "stars"),
    [([5], 5), ([4, 5], 5), ([4, 4, 5], 4), ([1, 2], 2), ([1, 1, 2], 1)],
)
def test_summary_stars_round_half_up(db, product, make_review, ratings, stars):
    for index, rating in enumerate(ratings):
        make_review(make_user(f"rater{index}"), product, rating=rating)

    assert product.reviews.summary().stars == stars


def test_newest_first(customer, named_customer, staff_user, product, make_review):
    now = timezone.now()
    oldest = make_review(customer, product, created_at=now - timedelta(days=9))
    newest = make_review(named_customer, product, created_at=now)
    middle = make_review(staff_user, product, created_at=now - timedelta(days=3))

    assert list(product.reviews.newest_first()) == [newest, middle, oldest]


# --- Admin -------------------------------------------------------------------


def test_review_is_registered_in_the_admin():
    assert admin.site.is_registered(Review)


def test_admin_changelist_loads(client, superuser, customer, product, make_review):
    make_review(customer, product)
    client.force_login(superuser)

    response = client.get("/admin/reviews/review/")

    assert response.status_code == 200
    assert "Seraphine Home Hub" in response.content.decode()
