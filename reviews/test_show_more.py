"""Show more reviews: the first ten on the product page, then ten at a time
from a public endpoint whose button replaces itself, with pinned reviews
excluded so no review ever appears twice."""

import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .models import REVIEWS_PER_BATCH, Review

HTMX = {"HX-Request": "true"}
CARD_ID = re.compile(r'id="review-(\d+)"')
MORE_URL = re.compile(r'hx-get="([^"]*/more/[^"]*)"')


@pytest.fixture
def reviews_of(db):
    """``reviews_of(product, n)``: n reviews by n new customers, one a day.

    Returned newest first, so ``[:10]`` is the first batch.
    """

    def build(product, count, *, prefix="reader"):
        now = timezone.now()
        reviews = []
        for i in range(count):
            user = get_user_model().objects.create_user(username=f"{prefix}{i}")
            reviews.append(
                Review.objects.create(
                    user=user,
                    product=product,
                    rating=4,
                    comment=f"Review number {i} of the batch.",
                    created_at=now - timedelta(days=i),
                )
            )
        return reviews

    return build


def more_url(product, query=""):
    return reverse("reviews:more", kwargs={"pk": product.pk}) + query


def card_pks(html):
    return [int(pk) for pk in CARD_ID.findall(html)]


def next_url(html):
    """The Show more button's URL, or ``None`` when there's no button."""
    match = MORE_URL.search(html)
    return match.group(1).replace("&amp;", "&") if match else None


def page_of(client, product):
    response = client.get(product.get_absolute_url())
    assert response.status_code == HTTPStatus.OK
    return response.content.decode()


def show_more(client, url):
    response = client.get(url, headers=HTMX)
    assert response.status_code == HTTPStatus.OK
    return response.content.decode()


def every_batch(client, product):
    """Follow Show more from the product page to the end: one list per batch."""
    html = page_of(client, product)
    batches = [card_pks(html)]
    url = next_url(html)
    while url:
        html = show_more(client, url)
        batches.append(card_pks(html))
        url = next_url(html)
    return batches


# --- The first batch, on the product page ----------------------------------


def test_batch_size_is_ten():
    assert REVIEWS_PER_BATCH == 10


def test_product_page_shows_the_ten_newest_reviews_newest_first(
    client, product, reviews_of
):
    reviews = reviews_of(product, 12)

    page = page_of(client, product)

    assert card_pks(page) == [review.pk for review in reviews[:10]]


def test_product_page_offers_show_more_when_more_remain(client, product, reviews_of):
    reviews_of(product, 11)

    page = page_of(client, product)

    assert "Show more reviews" in page
    assert next_url(page).startswith(more_url(product))


def test_no_show_more_with_exactly_ten_reviews(client, product, reviews_of):
    reviews_of(product, 10)

    page = page_of(client, product)

    assert len(card_pks(page)) == 10
    assert "Show more reviews" not in page
    assert next_url(page) is None


def test_no_show_more_without_reviews(client, product):
    page = page_of(client, product)

    assert "Show more reviews" not in page


def test_show_more_button_replaces_itself_in_place(client, product, reviews_of):
    reviews_of(product, 11)

    page = page_of(client, product)

    tag = re.search(r'<button[^>]*hx-get="[^"]*/more/[^>]*>', page).group(0)
    assert 'id="review-more"' in tag
    assert 'hx-target="this"' in tag
    assert 'hx-swap="outerHTML"' in tag
    assert 'hx-disabled-elt="this"' in tag
    # Inside the list, so the next batch lands after the last card.
    review_list = page[page.index('id="review-list"') :]
    assert 'id="review-more"' in review_list


# --- The endpoint ----------------------------------------------------------


def test_show_more_returns_the_next_batch_newest_first(client, product, reviews_of):
    reviews = reviews_of(product, 25)

    html = show_more(client, next_url(page_of(client, product)))

    assert card_pks(html) == [review.pk for review in reviews[10:20]]
    assert "Show more reviews" in html


def test_show_more_returns_a_partial_not_a_page(client, product, reviews_of):
    reviews_of(product, 11)

    response = client.get(next_url(page_of(client, product)), headers=HTMX)

    names = [template.name for template in response.templates]
    assert "reviews/partials/_review_batch.html" in names
    assert "base.html" not in names
    assert "<html" not in response.content.decode()


def test_button_disappears_on_the_last_batch(client, product, reviews_of):
    reviews = reviews_of(product, 25)

    batches = every_batch(client, product)

    assert [len(batch) for batch in batches] == [10, 10, 5]
    assert batches[-1] == [review.pk for review in reviews[20:]]


def test_last_batch_exactly_full_has_no_button(client, product, reviews_of):
    reviews_of(product, 20)

    batches = every_batch(client, product)

    assert [len(batch) for batch in batches] == [10, 10]


def test_every_review_appears_exactly_once_across_batches(client, product, reviews_of):
    reviews = reviews_of(product, 31)

    batches = every_batch(client, product)

    shown = [pk for batch in batches for pk in batch]
    assert shown == [review.pk for review in reviews]
    assert len(shown) == len(set(shown))


def test_reviews_sharing_a_timestamp_are_neither_skipped_nor_repeated(
    client, product, reviews_of
):
    reviews = reviews_of(product, 15)
    Review.objects.filter(pk__in=[r.pk for r in reviews]).update(
        created_at=timezone.now()
    )

    batches = every_batch(client, product)

    shown = [pk for batch in batches for pk in batch]
    assert sorted(shown) == sorted(review.pk for review in reviews)
    assert len(shown) == len(set(shown))


def test_a_review_posted_after_page_load_causes_no_duplicates(
    client, customer, product, reviews_of, make_review
):
    reviews = reviews_of(product, 12)
    page = page_of(client, product)
    make_review(customer, product, comment="Posted while the page was open.")

    html = show_more(client, next_url(page))

    assert card_pks(html) == [review.pk for review in reviews[10:]]


def test_show_more_still_works_after_the_last_shown_review_is_deleted(
    client, product, reviews_of
):
    reviews = reviews_of(product, 12)
    page = page_of(client, product)
    reviews[9].delete()

    html = show_more(client, next_url(page))

    assert card_pks(html) == [review.pk for review in reviews[10:]]


def test_show_more_lists_only_this_products_reviews(
    client, product, other_product, reviews_of
):
    reviews = reviews_of(product, 11)
    reviews_of(other_product, 5, prefix="elsewhere")

    html = show_more(client, next_url(page_of(client, product)))

    assert card_pks(html) == [reviews[10].pk]


def test_show_more_works_signed_out(client, product, reviews_of):
    reviews = reviews_of(product, 11)

    response = client.get(next_url(page_of(client, product)), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert "HX-Redirect" not in response
    assert card_pks(response.content.decode()) == [reviews[10].pk]


def test_show_more_works_for_an_unavailable_product(
    client, unavailable_product, reviews_of
):
    reviews = reviews_of(unavailable_product, 11)

    html = show_more(client, next_url(page_of(client, unavailable_product)))

    assert card_pks(html) == [reviews[10].pk]


def test_show_more_without_a_cursor_starts_from_the_newest(client, product, reviews_of):
    reviews = reviews_of(product, 12)

    html = show_more(client, more_url(product))

    assert card_pks(html) == [review.pk for review in reviews[:10]]


def test_a_malformed_cursor_starts_from_the_newest(client, product, reviews_of):
    reviews = reviews_of(product, 12)

    html = show_more(client, more_url(product, "?after=not-a-cursor"))

    assert card_pks(html) == [review.pk for review in reviews[:10]]


def test_show_more_is_get_only(client, product, reviews_of):
    reviews_of(product, 11)

    response = client.post(more_url(product), headers=HTMX)

    assert response.status_code == HTTPStatus.METHOD_NOT_ALLOWED


def test_show_more_for_a_deleted_product_is_an_inline_404(client, product, reviews_of):
    reviews_of(product, 11)
    url = next_url(page_of(client, product))
    product.delete()

    response = client.get(url, headers=HTMX)

    assert response.status_code == HTTPStatus.NOT_FOUND
    assert "This product is no longer available." in response.content.decode()
    assert response["HX-Retarget"] == "#review-more"
    assert response["HX-Reswap"] == "outerHTML"


def test_batches_keep_the_public_display_rules(
    client, named_customer, product, reviews_of, make_review
):
    make_review(
        named_customer,
        product,
        comment="<b>Oldest</b> of them all.",
        created_at=timezone.now() - timedelta(days=365),
    )
    reviews_of(product, 10)

    html = show_more(client, next_url(page_of(client, product)))

    assert "Margaret W." in html
    assert "Verified purchase" in html
    assert "&lt;b&gt;Oldest&lt;/b&gt;" in html
    assert "mwren_login" not in html
    assert "margaret.wren@example.com" not in html


def test_batch_cards_show_controls_only_to_their_author_and_staff(
    client, customer, staff_user, product, reviews_of
):
    reviews = reviews_of(product, 11)
    oldest = reviews[-1]

    client.force_login(customer)
    html = show_more(client, more_url(product))
    assert reverse("reviews:edit", kwargs={"pk": reviews[0].pk}) not in html

    client.force_login(staff_user)
    html = show_more(client, next_url(page_of(client, product)))
    assert reverse("reviews:edit", kwargs={"pk": oldest.pk}) in html
    assert reverse("reviews:delete_confirm", kwargs={"pk": oldest.pk}) in html


# --- The viewer's own review stays pinned ----------------------------------


def test_own_review_is_pinned_and_not_counted_in_the_first_batch(
    client, customer, product, reviews_of, make_review
):
    others = reviews_of(product, 12)
    own = make_review(
        customer,
        product,
        comment="My own words, pinned.",
        created_at=timezone.now() - timedelta(days=5),
    )
    client.force_login(customer)

    page = page_of(client, product)

    review_list = page[page.index('id="review-list"') :]
    assert card_pks(review_list) == [review.pk for review in others[:10]]
    assert card_pks(page).count(own.pk) == 1


def test_own_review_is_excluded_from_every_batch(
    client, customer, product, reviews_of, make_review
):
    others = reviews_of(product, 23)
    own = make_review(
        customer,
        product,
        comment="My own words, pinned.",
        created_at=timezone.now() - timedelta(days=15),
    )
    client.force_login(customer)

    batches = every_batch(client, product)

    shown = [pk for batch in batches for pk in batch]
    assert shown.count(own.pk) == 1  # once, in the form slot on the page
    assert [pk for pk in shown if pk != own.pk] == [review.pk for review in others]
    assert [len(batch) for batch in batches[1:]] == [10, 3]


def test_own_review_is_excluded_even_from_a_cursorless_request(
    client, customer, product, reviews_of, make_review
):
    reviews_of(product, 3)
    own = make_review(customer, product, created_at=timezone.now())
    client.force_login(customer)

    html = show_more(client, more_url(product))

    assert own.pk not in card_pks(html)
    assert len(card_pks(html)) == 3


def test_another_viewers_review_is_not_excluded(
    client, customer, staff_user, product, reviews_of, make_review
):
    reviews_of(product, 10)
    oldest = make_review(
        customer, product, created_at=timezone.now() - timedelta(days=365)
    )
    client.force_login(staff_user)

    html = show_more(client, next_url(page_of(client, product)))

    assert card_pks(html) == [oldest.pk]


# --- The queryset -----------------------------------------------------------


def test_batch_returns_reviews_and_whether_more_remain(product, reviews_of):
    reviews = reviews_of(product, 12)

    first = product.reviews.batch()
    second = product.reviews.batch(after=first.cursor)

    assert [r.pk for r in first.reviews] == [r.pk for r in reviews[:10]]
    assert first.has_more is True
    assert [r.pk for r in second.reviews] == [r.pk for r in reviews[10:]]
    assert second.has_more is False


def test_batch_excludes_pinned_reviews(product, reviews_of):
    reviews = reviews_of(product, 12)
    pinned = [reviews[0], reviews[11]]

    batch = product.reviews.excluding(*pinned).batch()

    assert [r.pk for r in batch.reviews] == [r.pk for r in reviews[1:11]]
    assert batch.has_more is False
