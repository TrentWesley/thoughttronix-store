"""The seed's review demo data, checked as data.

Tests never invoke the seed command, so these read the seed module's
constants instead: the agreed shape of the review demo world (PRD stories
64–70) is visible there without running anything. The seed itself also
refuses, at run time, to create any review the store's own eligibility
rule would refuse.
"""

from collections import Counter
from decimal import Decimal

from orders.models import Order
from products.management.commands import seed

from .models import COMMENT_MAX_LENGTH, COMMENT_MIN_LENGTH, Review

REVIEWS = getattr(seed, "REVIEWS", [])
REVIEW_ORDERS = getattr(seed, "REVIEW_ORDERS", [])
REVIEWER_CUSTOMERS = getattr(seed, "REVIEWER_CUSTOMERS", [])
SHOWCASE_SLUG = getattr(seed, "SHOWCASE_SLUG", None)
STAFF_EDITED_REVIEW = getattr(seed, "STAFF_EDITED_REVIEW", None)

CATALOG_PRICES = {
    seed.slugify(name): (category, price)
    for category, entries in seed.CATALOG.items()
    for name, price, *_ in entries
}


def review_keys():
    return [(username, slug) for username, slug, *_ in REVIEWS]


def showcase_reviewers():
    return [username for username, slug in review_keys() if slug == SHOWCASE_SLUG]


def test_seed_defines_15_to_25_reviews():
    assert 15 <= len(REVIEWS) <= 25


def test_one_seeded_review_per_user_per_product():
    assert len(set(review_keys())) == len(REVIEWS)


def test_seeded_reviews_are_valid_reviews():
    ratings = {choice.value for choice in Review.Rating}
    for username, slug, rating, _days_after, comment in REVIEWS:
        assert rating in ratings, (username, slug)
        assert COMMENT_MIN_LENGTH <= len(comment) <= COMMENT_MAX_LENGTH
        assert comment == comment.strip()


def test_seeded_reviews_are_by_known_users_of_real_products():
    usernames = (
        {username for username, *_ in seed.DEMO_USERS}
        | {username for username, *_ in seed.BACKGROUND_CUSTOMERS}
        | {username for username, *_ in REVIEWER_CUSTOMERS}
    )
    for username, slug in review_keys():
        assert username in usernames
        assert slug in CATALOG_PRICES


def test_4_or_5_reviewer_only_customers_separate_from_the_background_pool():
    """Separate, so the background orders' seeded random draws don't move."""
    assert 4 <= len(REVIEWER_CUSTOMERS) <= 5
    background = {username for username, *_ in seed.BACKGROUND_CUSTOMERS}
    demo = {username for username, *_ in seed.DEMO_USERS}
    for username, *_ in REVIEWER_CUSTOMERS:
        assert username not in background | demo


def test_the_showcase_product_is_inexpensive_and_not_defense():
    category, price = CATALOG_PRICES[SHOWCASE_SLUG]
    assert category != "Defense"
    assert price < Decimal("100.00")


def test_the_showcase_product_has_12_or_13_reviews_mostly_not_the_demo_customer():
    """Enough that "Show more reviews" appears for every viewer."""
    reviewers = showcase_reviewers()
    assert 12 <= len(reviewers) <= 13
    assert len([username for username in reviewers if username != "customer"]) >= 11


def test_reviewer_only_and_background_customers_review_the_showcase():
    reviewers = set(showcase_reviewers())
    background = {username for username, *_ in seed.BACKGROUND_CUSTOMERS}
    assert {username for username, *_ in REVIEWER_CUSTOMERS} <= reviewers
    assert reviewers & background


def test_every_showcase_reviewer_gets_a_cheap_delivered_showcase_order():
    ordered = Counter(
        username for username, _days_ago, slug in REVIEW_ORDERS if slug == SHOWCASE_SLUG
    )
    assert all(ordered[username] == 1 for username in showcase_reviewers())


def test_review_orders_are_cheap_recent_history_and_never_defense():
    """Barely moves dashboard revenue: no SoulSear spike."""
    assert REVIEW_ORDERS
    for username, days_ago, slug in REVIEW_ORDERS:
        category, price = CATALOG_PRICES[slug]
        assert category != "Defense", slug
        assert price < Decimal("100.00"), slug
        # Delivered orders are older than two weeks, like the background ones.
        assert 14 < days_ago <= 182, (username, days_ago)
    total = sum(CATALOG_PRICES[slug][1] for _user, _days, slug in REVIEW_ORDERS)
    assert total < Decimal("1000.00")


def test_the_demo_customer_has_a_delivered_authorization_case_but_no_review():
    assert ("customer", "soulsear-authorization-case") in {
        (username, slug) for username, _days_ago, slug in REVIEW_ORDERS
    }
    assert CATALOG_PRICES["soulsear-authorization-case"][1] == Decimal("39.00")
    assert ("customer", "soulsear-authorization-case") not in review_keys()


def test_dreamweaver_and_the_authorization_case_stay_unreviewed():
    reviewed = {slug for _username, slug in review_keys()}
    assert "dreamweaver" not in reviewed
    assert "soulsear-authorization-case" not in reviewed


def test_the_demo_customer_reviews_something_from_their_delivered_orders():
    delivered = {
        slug
        for _days_ago, status, lines in seed.CUSTOMER_ORDERS
        if status == Order.Status.DELIVERED
        for slug, _quantity in lines
    }
    reviewed = {slug for username, slug in review_keys() if username == "customer"}
    assert reviewed
    assert reviewed <= delivered


def test_exactly_one_seeded_review_is_marked_as_edited_by_staff():
    """A customer's review, so the "Edited by ThoughtTronix staff" label is true."""
    assert STAFF_EDITED_REVIEW in review_keys()
    staff = {
        username for username, *_, is_staff, _su, _job in seed.DEMO_USERS if is_staff
    }
    assert STAFF_EDITED_REVIEW[0] not in staff
