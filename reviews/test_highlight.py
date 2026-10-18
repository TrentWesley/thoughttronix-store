"""Highlighting: ``?review=<pk>`` on a product page pins that review below
the viewer's own, with a subtle highlight, and keeps it out of every batch.
It changes display only, and a bad id is ignored silently."""

import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .models import Review

HTMX = {"HX-Request": "true"}
CARD_ID = re.compile(r'id="review-(\d+)"')
MORE_URL = re.compile(r'hx-get="([^"]*/more/[^"]*)"')


@pytest.fixture
def reviews_of(db):
    """``reviews_of(product, n)``: n reviews by new customers, newest first."""

    def build(product, count, *, prefix="reader"):
        now = timezone.now()
        return [
            Review.objects.create(
                user=get_user_model().objects.create_user(username=f"{prefix}{i}"),
                product=product,
                rating=4,
                comment=f"Review number {i} of the batch.",
                created_at=now - timedelta(days=i),
            )
            for i in range(count)
        ]

    return build


def page_of(client, product, query=""):
    response = client.get(product.get_absolute_url() + query)
    assert response.status_code == HTTPStatus.OK
    return response.content.decode()


def card_pks(html):
    return [int(pk) for pk in CARD_ID.findall(html)]


def next_url(html):
    match = MORE_URL.search(html)
    return match.group(1).replace("&amp;", "&") if match else None


def every_batch(client, product, query=""):
    """Follow Show more from the product page to the end: one list per batch."""
    html = page_of(client, product, query)
    batches = [card_pks(html)]
    url = next_url(html)
    while url:
        response = client.get(url, headers=HTMX)
        assert response.status_code == HTTPStatus.OK
        html = response.content.decode()
        batches.append(card_pks(html))
        url = next_url(html)
    return batches


def highlight_section(html):
    """The highlight wrapper's markup, or ``None`` when nothing is highlighted."""
    match = re.search(r'<div id="review-highlight".*?</article>\s*</div>', html, re.S)
    return match.group(0) if match else None


# --- Pinned and highlighted ------------------------------------------------


def test_highlighted_review_is_pinned_with_a_highlight(client, product, reviews_of):
    reviews = reviews_of(product, 3)
    target = reviews[2]

    page = page_of(client, product, f"?review={target.pk}")

    section = highlight_section(page)
    assert section is not None
    assert card_pks(section) == [target.pk]
    # First in the list, ahead of the newer reviews, and shown only once.
    review_list = page[page.index('id="review-list"') :]
    assert card_pks(review_list)[0] == target.pk
    assert card_pks(page).count(target.pk) == 1


def test_no_highlight_without_the_parameter(client, product, reviews_of):
    reviews_of(product, 3)

    assert highlight_section(page_of(client, product)) is None


def test_a_highlighted_review_older_than_the_first_ten_still_appears_pinned(
    client, product, reviews_of
):
    reviews = reviews_of(product, 25)
    oldest = reviews[-1]

    page = page_of(client, product, f"?review={oldest.pk}")

    assert card_pks(highlight_section(page)) == [oldest.pk]
    # The first batch is still ten others, newest first.
    others = [pk for pk in card_pks(page) if pk != oldest.pk]
    assert others == [review.pk for review in reviews[:10]]


def test_highlighted_review_is_excluded_from_every_batch(client, product, reviews_of):
    reviews = reviews_of(product, 25)
    target = reviews[4]

    batches = every_batch(client, product, f"?review={target.pk}")

    shown = [pk for batch in batches for pk in batch]
    assert shown.count(target.pk) == 1
    assert [pk for pk in shown if pk != target.pk] == [
        review.pk for review in reviews if review != target
    ]
    assert [len(batch) for batch in batches] == [11, 10, 4]


def test_show_more_keeps_excluding_the_highlighted_review(client, product, reviews_of):
    reviews = reviews_of(product, 12)
    target = reviews[0]  # the newest, so a cursorless batch would include it
    url = reverse("reviews:more", kwargs={"pk": product.pk})

    response = client.get(f"{url}?review={target.pk}", headers=HTMX)

    assert card_pks(response.content.decode()) == [r.pk for r in reviews[1:11]]


def test_highlighted_review_is_pinned_below_the_viewers_own(
    client, customer, product, reviews_of, make_review
):
    reviews = reviews_of(product, 3)
    own = make_review(customer, product, created_at=timezone.now() - timedelta(days=9))
    target = reviews[1]
    client.force_login(customer)

    page = page_of(client, product, f"?review={target.pk}")

    order = card_pks(page)
    assert order[:2] == [own.pk, target.pk]
    assert order.count(own.pk) == order.count(target.pk) == 1
    assert page.index('id="review-form-slot"') < page.index('id="review-highlight"')


def test_own_and_highlighted_review_being_the_same_appears_once(
    client, customer, product, reviews_of, make_review
):
    reviews_of(product, 12)
    own = make_review(customer, product, created_at=timezone.now() - timedelta(days=30))
    client.force_login(customer)

    batches = every_batch(client, product, f"?review={own.pk}")

    shown = [pk for batch in batches for pk in batch]
    assert shown.count(own.pk) == 1
    assert len(shown) == 13
    assert highlight_section(page_of(client, product, f"?review={own.pk}")) is None


def test_staff_get_edit_and_delete_controls_on_the_highlighted_review(
    client, staff_user, product, reviews_of
):
    reviews = reviews_of(product, 15)
    target = reviews[-1]
    client.force_login(staff_user)

    section = highlight_section(page_of(client, product, f"?review={target.pk}"))

    assert reverse("reviews:edit", kwargs={"pk": target.pk}) in section
    assert reverse("reviews:delete_confirm", kwargs={"pk": target.pk}) in section


def test_highlighting_grants_no_permissions(client, customer, product, reviews_of):
    reviews = reviews_of(product, 3)
    target = reviews[0]
    client.force_login(customer)

    section = highlight_section(page_of(client, product, f"?review={target.pk}"))

    assert reverse("reviews:edit", kwargs={"pk": target.pk}) not in section
    assert reverse("reviews:delete_confirm", kwargs={"pk": target.pk}) not in section


def test_highlighting_works_signed_out_and_keeps_public_display_rules(
    client, named_customer, product, make_review
):
    review = make_review(named_customer, product)

    section = highlight_section(page_of(client, product, f"?review={review.pk}"))

    assert "Margaret W." in section
    assert "mwren_login" not in section


# --- Bad ids are ignored ---------------------------------------------------


@pytest.mark.parametrize(
    "value", ["", "abc", "1.5", "-3", "0", "99999999999999999999999", "%00"]
)
def test_malformed_ids_are_ignored(client, product, reviews_of, value):
    reviews = reviews_of(product, 12)

    page = page_of(client, product, f"?review={value}")

    assert highlight_section(page) is None
    assert card_pks(page) == [review.pk for review in reviews[:10]]


def test_another_products_review_is_ignored(
    client, customer, product, other_product, reviews_of, make_review
):
    reviews = reviews_of(product, 12)
    elsewhere = make_review(customer, other_product)

    page = page_of(client, product, f"?review={elsewhere.pk}")

    assert highlight_section(page) is None
    assert elsewhere.pk not in card_pks(page)
    assert card_pks(page) == [review.pk for review in reviews[:10]]


def test_a_deleted_review_is_ignored(client, product, reviews_of):
    reviews = reviews_of(product, 12)
    gone = reviews.pop()
    gone_pk = gone.pk
    gone.delete()

    page = page_of(client, product, f"?review={gone_pk}")

    assert highlight_section(page) is None
    assert card_pks(page) == [review.pk for review in reviews[:10]]


def test_show_more_ignores_a_bad_highlight(client, product, reviews_of):
    reviews = reviews_of(product, 12)
    url = reverse("reviews:more", kwargs={"pk": product.pk})

    response = client.get(f"{url}?review=nope", headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert card_pks(response.content.decode()) == [r.pk for r in reviews[:10]]
