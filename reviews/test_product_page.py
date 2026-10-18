"""The read-only Reviews section on the public product page."""

from datetime import UTC, datetime, timedelta

from django.utils import timezone


def page_of(client, product):
    response = client.get(product.get_absolute_url())
    assert response.status_code == 200
    return response.content.decode()


def test_product_page_has_a_reviews_section(client, product):
    page = page_of(client, product)

    assert 'id="reviews"' in page
    assert "Reviews" in page


def test_no_reviews_yet(client, product):
    page = page_of(client, product)

    assert "No reviews yet" in page


def test_summary_shows_average_and_count(
    client, customer, named_customer, product, make_review
):
    make_review(customer, product, rating=5)
    make_review(named_customer, product, rating=4)

    page = page_of(client, product)

    assert "No reviews yet" not in page
    assert "4.5 out of 5" in page
    assert "2 reviews" in page


def test_summary_says_one_review_in_the_singular(
    client, customer, product, make_review
):
    make_review(customer, product, rating=3)

    page = page_of(client, product)

    assert "3.0 out of 5" in page
    assert "1 review<" in page


def test_card_shows_rating_comment_name_date_and_badge(
    client, named_customer, product, make_review
):
    review = make_review(
        named_customer,
        product,
        rating=4,
        comment="She hears everything. Even the things I didn't say.",
        created_at=datetime(2026, 9, 14, 12, tzinfo=UTC),
    )

    page = page_of(client, product)

    assert f'id="review-{review.pk}"' in page
    assert "Rated 4 out of 5" in page
    assert "She hears everything. Even the things I didn&#x27;t say." in page
    assert "Margaret W." in page
    assert "September 14, 2026" in page
    assert "Verified purchase" in page


def test_reviews_are_listed_newest_first(
    client, customer, named_customer, staff_user, product, make_review
):
    now = timezone.now()
    make_review(
        customer,
        product,
        comment="The oldest review.",
        created_at=now - timedelta(days=9),
    )
    make_review(named_customer, product, comment="The newest review.", created_at=now)
    make_review(
        staff_user,
        product,
        comment="The middle review.",
        created_at=now - timedelta(days=3),
    )

    page = page_of(client, product)

    assert (
        page.index("The newest review.")
        < page.index("The middle review.")
        < page.index("The oldest review.")
    )


def test_every_card_has_the_verified_purchase_badge(
    client, customer, named_customer, product, make_review
):
    make_review(customer, product)
    make_review(named_customer, product)

    page = page_of(client, product)

    assert page.count("Verified purchase") == 2


def test_only_this_products_reviews_appear(
    client, customer, product, other_product, make_review
):
    make_review(customer, product, comment="About the hub itself.")
    make_review(customer, other_product, comment="About the pillow instead.")

    page = page_of(client, product)

    assert "About the hub itself." in page
    assert "About the pillow instead." not in page


def test_comments_are_autoescaped(client, customer, product, make_review):
    make_review(customer, product, comment="<script>alert('pwned')</script>")

    page = page_of(client, product)

    assert "<script>alert" not in page
    assert "&lt;script&gt;alert(&#x27;pwned&#x27;)&lt;/script&gt;" in page


def test_comment_line_breaks_are_preserved(client, customer, product, make_review):
    make_review(customer, product, comment="First line here.\nSecond line here.")

    page = page_of(client, product)

    assert "First line here.<br>Second line here." in page


def test_public_page_never_shows_username_email_or_last_name(
    client, named_customer, product, make_review
):
    make_review(named_customer, product)

    page = page_of(client, product)

    assert "Margaret W." in page
    assert "mwren_login" not in page
    assert "margaret.wren@example.com" not in page
    assert "Wren" not in page


def test_reviewer_without_a_first_name_is_a_verified_customer(
    client, customer, product, make_review
):
    make_review(customer, product)

    page = page_of(client, product)

    assert "Verified customer" in page
    assert ">customer<" not in page


def test_unavailable_product_reviews_are_readable_signed_out(
    client, customer, unavailable_product, make_review
):
    make_review(customer, unavailable_product, comment="Recalled, but I loved it.")

    page = page_of(client, unavailable_product)

    assert "Recalled, but I loved it." in page
    assert "Verified purchase" in page


def test_signed_in_visitors_see_the_reviews_too(
    client, customer, named_customer, product, make_review
):
    make_review(named_customer, product, comment="Signed-in readers see this.")
    client.force_login(customer)

    page = page_of(client, product)

    assert "Signed-in readers see this." in page
