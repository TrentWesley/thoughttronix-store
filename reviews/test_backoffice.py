"""The back office's read-only Reviews tab, and the review count on the
product delete confirmation."""

import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone

from .models import Review

LIST_URL = "/backoffice/reviews/"
ROW_LINK = re.compile(r'href="([^"]*\?review=\d+#review-\d+)"')


@pytest.fixture
def many_reviews(db, product):
    """``many_reviews(n)``: n reviews of ``product``, one a day, newest first."""

    def build(count):
        now = timezone.now()
        return [
            Review.objects.create(
                user=get_user_model().objects.create_user(username=f"critic{i}"),
                product=product,
                rating=3,
                comment=f"Back-office review number {i}.",
                created_at=now - timedelta(days=i),
            )
            for i in range(count)
        ]

    return build


def test_url_is_named_and_under_the_back_office():
    assert reverse("reviews:manage_reviews") == LIST_URL


# --- Access ----------------------------------------------------------------


def test_anonymous_visitors_are_sent_to_sign_in(client):
    response = client.get(LIST_URL)

    assert response.status_code == HTTPStatus.FOUND
    assert response.url.startswith(reverse("accounts:login"))


def test_customers_are_forbidden(client, customer):
    client.force_login(customer)

    assert client.get(LIST_URL).status_code == HTTPStatus.FORBIDDEN


def test_staff_can_open_the_reviews_tab(client, staff_user):
    client.force_login(staff_user)

    response = client.get(LIST_URL)

    assert response.status_code == HTTPStatus.OK
    assert "backoffice/base.html" in [t.name for t in response.templates]
    assert response.context["section"] == "reviews"


def test_tab_rail_has_an_active_reviews_tab(client, staff_user):
    client.force_login(staff_user)

    html = client.get(LIST_URL).content.decode()

    tab = re.search(r'<a role="tab"[^>]*href="/backoffice/reviews/"[^>]*>', html)
    assert tab is not None
    assert "tab-active" in tab.group(0)


def test_reviews_tab_is_inactive_on_other_back_office_pages(client, staff_user):
    client.force_login(staff_user)

    html = client.get(reverse("products:manage_products")).content.decode()

    tab = re.search(r'<a role="tab"[^>]*href="/backoffice/reviews/"[^>]*>', html)
    assert tab is not None
    assert "tab-active" not in tab.group(0)


# --- The list --------------------------------------------------------------


def test_empty_state(client, staff_user):
    client.force_login(staff_user)

    html = client.get(LIST_URL).content.decode()

    assert "No reviews yet" in html
    assert "<table" not in html


def test_rows_show_the_agreed_columns(
    client, staff_user, named_customer, product, make_review
):
    review = make_review(
        named_customer,
        product,
        rating=2,
        comment="It listened to my thoughts and then " + "kept going " * 20,
    )
    client.force_login(staff_user)

    html = client.get(LIST_URL).content.decode()

    assert product.name in html
    assert "mwren_login" in html  # staff-only, so the username is fine here
    assert 'aria-label="Rated 2 out of 5"' in html
    assert "It listened to my thoughts and then" in html
    assert review.comment not in html  # an excerpt, not the whole comment
    assert review.created_at.strftime("%b") in html


def test_comments_are_autoescaped(client, staff_user, customer, product, make_review):
    make_review(customer, product, comment="<script>alert('hi')</script> nope")
    client.force_login(staff_user)

    html = client.get(LIST_URL).content.decode()

    assert "<script>alert" not in html
    assert "&lt;script&gt;" in html


def test_reviews_are_listed_newest_first(client, staff_user, many_reviews):
    reviews = many_reviews(3)
    client.force_login(staff_user)

    response = client.get(LIST_URL)

    assert list(response.context["reviews"]) == reviews


def test_lists_reviews_of_every_product_including_unavailable(
    client, staff_user, customer, product, unavailable_product, make_review
):
    make_review(customer, product)
    make_review(customer, unavailable_product)
    client.force_login(staff_user)

    response = client.get(LIST_URL)

    assert len(response.context["reviews"]) == 2


def test_list_is_paginated(client, staff_user, many_reviews):
    reviews = many_reviews(25)
    client.force_login(staff_user)

    first = client.get(LIST_URL)
    second = client.get(LIST_URL + "?page=2")

    assert first.context["is_paginated"]
    assert list(first.context["reviews"]) == reviews[:20]
    assert list(second.context["reviews"]) == reviews[20:]
    assert "Page 1 of 2" in first.content.decode()


def test_rows_link_to_the_highlighted_review_on_its_product_page(
    client, staff_user, customer, product, make_review
):
    review = make_review(customer, product)
    client.force_login(staff_user)

    html = client.get(LIST_URL).content.decode()

    expected = f"{product.get_absolute_url()}?review={review.pk}#review-{review.pk}"
    assert ROW_LINK.findall(html) == [expected]
    assert review.get_absolute_url() == expected


def test_the_list_has_no_edit_or_delete_controls(
    client, staff_user, customer, product, make_review
):
    review = make_review(customer, product)
    client.force_login(staff_user)

    html = client.get(LIST_URL).content.decode()

    assert reverse("reviews:edit", kwargs={"pk": review.pk}) not in html
    assert reverse("reviews:delete_confirm", kwargs={"pk": review.pk}) not in html


def test_the_list_is_read_only(client, staff_user):
    client.force_login(staff_user)

    assert client.post(LIST_URL).status_code == HTTPStatus.METHOD_NOT_ALLOWED


# --- Product delete confirmation -------------------------------------------


def delete_page(client, product):
    url = reverse("products:manage_product_delete", kwargs={"pk": product.pk})
    return client.get(url).content.decode()


def test_product_delete_confirmation_counts_its_reviews(
    client, staff_user, product, other_product, many_reviews, make_review
):
    many_reviews(3)
    make_review(staff_user, other_product)  # another product's: not counted
    client.force_login(staff_user)

    html = delete_page(client, product)

    assert "3 reviews will also be deleted" in html


def test_product_delete_confirmation_with_one_review(
    client, staff_user, customer, product, make_review
):
    make_review(customer, product)
    client.force_login(staff_user)

    assert "1 review will also be deleted" in delete_page(client, product)


def test_product_delete_confirmation_with_no_reviews(client, staff_user, product):
    client.force_login(staff_user)

    assert "No reviews will be deleted" in delete_page(client, product)
