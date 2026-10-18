"""Editing a review in place: the edit form, Save and Cancel, edit tracking,
and ownership enforced by the lookup."""

import re
from datetime import timedelta
from http import HTTPStatus

import pytest
from django.urls import reverse
from django.utils import timezone

from orders.models import Order

from .forms import ReviewForm
from .models import Review

HTMX = {"HX-Request": "true"}
ORIGINAL = "The original words, exactly as posted."
CHANGED = {"rating": "2", "comment": "On reflection, she listens too much."}


def edit_url(review):
    return reverse("reviews:edit", kwargs={"pk": review.pk})


def update_url(review):
    return reverse("reviews:update", kwargs={"pk": review.pk})


def cancel_url(review):
    return reverse("reviews:cancel_edit", kwargs={"pk": review.pk})


def template_names(response):
    return [template.name for template in response.templates]


def has_oob_summary(html):
    return re.search(r'id="review-summary"[^>]*hx-swap-oob="true"', html) is not None


def page_of(client, product):
    response = client.get(product.get_absolute_url())
    assert response.status_code == HTTPStatus.OK
    return response.content.decode()


def card_html(page, review):
    """The markup of one review card, up to its closing ``</article>``."""
    start = page.index(f'id="review-{review.pk}"')
    return page[start : page.index("</article>", start)]


@pytest.fixture
def review(customer, product, make_review):
    """The customer's own 4-star review, posted a week ago."""
    return make_review(
        customer,
        product,
        rating=4,
        comment=ORIGINAL,
        created_at=timezone.now() - timedelta(days=7),
    )


# --- Edit buttons ------------------------------------------------------------


def test_author_sees_edit_on_their_own_review(client, customer, review):
    client.force_login(customer)

    card = card_html(page_of(client, review.product), review)

    assert f'hx-get="{edit_url(review)}"' in card
    assert f'hx-target="#review-{review.pk}"' in card


def test_staff_see_edit_on_every_review(client, staff_user, review):
    client.force_login(staff_user)

    card = card_html(page_of(client, review.product), review)

    assert f'hx-get="{edit_url(review)}"' in card


def test_no_edit_on_other_customers_reviews(client, named_customer, review):
    client.force_login(named_customer)

    page = page_of(client, review.product)

    assert edit_url(review) not in page


def test_no_edit_for_signed_out_visitors(client, review):
    assert edit_url(review) not in page_of(client, review.product)


# --- Edit form, Save, Cancel ------------------------------------------------


def test_edit_returns_the_prefilled_form_in_place_of_the_card(client, customer, review):
    client.force_login(customer)

    response = client.get(edit_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    names = template_names(response)
    assert "reviews/partials/_review_form.html" in names
    assert "base.html" not in names
    html = response.content.decode()
    assert f'id="review-{review.pk}"' in html
    assert f'hx-post="{update_url(review)}"' in html
    assert f'hx-get="{cancel_url(review)}"' in html
    assert "hx-disabled-elt=" in html
    assert ORIGINAL in html
    assert re.search(r'value="4"[^>]*checked', html)
    assert reverse("reviews:create", kwargs={"pk": review.product.pk}) not in html


def test_save_button_is_disabled_while_saving(client, customer, review):
    client.force_login(customer)

    html = client.get(edit_url(review), headers=HTMX).content.decode()

    form = re.search(rf'<form[^>]*hx-post="{update_url(review)}"[^>]*>', html)
    assert form is not None
    assert "hx-disabled-elt=\"find button[type='submit']\"" in form.group()
    assert re.findall(r'<button type="submit"[^>]*>([^<]*)</button>', html) == ["Save"]


def test_edit_form_changes_nothing(client, customer, review):
    client.force_login(customer)

    client.get(edit_url(review), headers=HTMX)

    review.refresh_from_db()
    assert review.comment == ORIGINAL
    assert review.edited_at is None


def test_update_saves_and_returns_the_card_with_the_summary_oob(
    client, customer, named_customer, review, make_review
):
    make_review(named_customer, review.product, rating=4)
    client.force_login(customer)

    response = client.post(update_url(review), CHANGED, headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    review.refresh_from_db()
    assert (review.rating, review.comment) == (2, CHANGED["comment"])
    names = template_names(response)
    assert "reviews/partials/_review_card.html" in names
    assert "base.html" not in names
    html = response.content.decode()
    assert f'id="review-{review.pk}"' in html
    assert CHANGED["comment"] in html
    assert 'name="comment"' not in html
    assert has_oob_summary(html)
    assert "3.0 out of 5" in html
    assert "2 reviews" in html


def test_update_trims_the_comment(client, customer, review):
    client.force_login(customer)

    client.post(
        update_url(review),
        {"rating": "5", "comment": "   Trimmed on the way in.   "},
        headers=HTMX,
    )

    review.refresh_from_db()
    assert review.comment == "Trimmed on the way in."


def test_invalid_update_rerenders_the_form_with_errors_and_saves_nothing(
    client, customer, review
):
    client.force_login(customer)

    response = client.post(
        update_url(review), {"rating": "3", "comment": "   "}, headers=HTMX
    )

    assert response.status_code == HTTPStatus.OK
    assert "reviews/partials/_review_form.html" in template_names(response)
    html = response.content.decode()
    assert "This field is required." in html
    assert f'hx-post="{update_url(review)}"' in html
    assert re.search(r'value="3"[^>]*checked', html)
    assert not has_oob_summary(html)
    review.refresh_from_db()
    assert (review.rating, review.comment, review.edited_at) == (4, ORIGINAL, None)


def test_cancel_returns_the_unchanged_card(client, customer, review):
    client.force_login(customer)

    response = client.get(cancel_url(review), headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    assert "reviews/partials/_review_card.html" in template_names(response)
    html = response.content.decode()
    assert f'id="review-{review.pk}"' in html
    assert ORIGINAL in html
    assert 'name="comment"' not in html
    review.refresh_from_db()
    assert review.edited_at is None


@pytest.mark.parametrize("url", [edit_url, cancel_url])
def test_update_is_post_only_and_the_others_get_only(client, customer, review, url):
    client.force_login(customer)

    assert client.get(update_url(review), headers=HTMX).status_code == 405
    assert client.post(url(review), CHANGED, headers=HTMX).status_code == 405
    review.refresh_from_db()
    assert review.comment == ORIGINAL


# --- Edit tracking -----------------------------------------------------------


def test_a_new_review_has_no_edited_label(client, review):
    card = card_html(page_of(client, review.product), review)

    assert "Edited" not in card


def test_a_customer_edit_sets_edited_at_only(client, customer, review):
    client.force_login(customer)

    response = client.post(update_url(review), CHANGED, headers=HTMX)

    review.refresh_from_db()
    assert review.edited_at is not None
    assert review.edited_by_staff_at is None
    html = response.content.decode()
    assert "Edited" in html
    assert "Edited by ThoughtTronix staff" not in html


def test_a_staff_edit_of_another_users_review_sets_the_staff_label(
    client, staff_user, review
):
    client.force_login(staff_user)

    response = client.post(update_url(review), CHANGED, headers=HTMX)

    review.refresh_from_db()
    assert review.edited_at is not None
    assert review.edited_by_staff_at is not None
    assert review.user != staff_user
    assert "Edited by ThoughtTronix staff" in response.content.decode()


def test_a_staff_edit_of_their_own_review_is_an_author_edit(
    client, staff_user, product, make_review
):
    own = make_review(staff_user, product, comment=ORIGINAL)
    client.force_login(staff_user)

    response = client.post(update_url(own), CHANGED, headers=HTMX)

    own.refresh_from_db()
    assert own.edited_at is not None
    assert own.edited_by_staff_at is None
    assert "Edited by ThoughtTronix staff" not in response.content.decode()


def test_an_author_edit_clears_the_staff_label(client, customer, review):
    staff_edit = timezone.now() - timedelta(days=1)
    Review.objects.filter(pk=review.pk).update(
        edited_at=staff_edit, edited_by_staff_at=staff_edit
    )
    client.force_login(customer)

    response = client.post(update_url(review), CHANGED, headers=HTMX)

    review.refresh_from_db()
    assert review.edited_by_staff_at is None
    assert review.edited_at > staff_edit
    html = response.content.decode()
    assert "Edited by ThoughtTronix staff" not in html
    assert "Edited" in html


def test_staff_label_shows_on_the_public_page(client, review):
    when = timezone.now()
    Review.objects.filter(pk=review.pk).update(edited_at=when, edited_by_staff_at=when)

    card = card_html(page_of(client, review.product), review)

    assert "Edited by ThoughtTronix staff" in card


def has_edited_label(html):
    """The plain "Edited" label, told apart from the staff label."""
    return re.search(r">\s*Edited\s*<", html) is not None


def test_a_staff_edited_review_shows_both_labels(client, review):
    when = timezone.now()
    Review.objects.filter(pk=review.pk).update(edited_at=when, edited_by_staff_at=when)

    card = card_html(page_of(client, review.product), review)

    assert has_edited_label(card)
    assert "Edited by ThoughtTronix staff" in card


def test_a_staff_edit_response_shows_both_labels(client, staff_user, review):
    client.force_login(staff_user)

    html = client.post(update_url(review), CHANGED, headers=HTMX).content.decode()

    assert has_edited_label(html)
    assert "Edited by ThoughtTronix staff" in html


def test_an_author_edited_review_shows_only_the_edited_label(client, review):
    Review.objects.filter(pk=review.pk).update(edited_at=timezone.now())

    card = card_html(page_of(client, review.product), review)

    assert has_edited_label(card)
    assert "Edited by ThoughtTronix staff" not in card


def test_saving_with_no_changes_is_not_an_edit(client, staff_user, review):
    client.force_login(staff_user)

    response = client.post(
        update_url(review), {"rating": "4", "comment": ORIGINAL}, headers=HTMX
    )

    assert response.status_code == HTTPStatus.OK
    review.refresh_from_db()
    assert (review.edited_at, review.edited_by_staff_at) == (None, None)


def test_the_form_records_edits_in_its_save_path(customer, staff_user, review):
    form = ReviewForm(CHANGED, instance=review, editor=staff_user)
    assert form.is_valid()

    form.save()

    review.refresh_from_db()
    assert review.edited_at is not None
    assert review.edited_by_staff_at is not None


def test_creating_through_the_form_is_not_an_edit(customer, product):
    form = ReviewForm(
        CHANGED, instance=Review(user=customer, product=product), editor=customer
    )
    assert form.is_valid()

    review = form.save()

    assert (review.edited_at, review.edited_by_staff_at) == (None, None)


# --- Ownership is enforced by the lookup ------------------------------------


def assert_review_alert(response, review):
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response["HX-Retarget"] == f"#review-{review.pk}"
    assert response["HX-Reswap"] == "outerHTML"
    assert "reviews/partials/_alert.html" in template_names(response)
    html = response.content.decode()
    assert 'role="alert"' in html
    assert "This review is no longer available." in html
    return html


def test_another_customer_gets_404_for_the_edit_form(client, named_customer, review):
    client.force_login(named_customer)

    response = client.get(edit_url(review), headers=HTMX)

    html = assert_review_alert(response, review)
    assert ORIGINAL not in html


def test_another_customer_gets_404_for_the_update_and_nothing_changes(
    client, named_customer, review
):
    client.force_login(named_customer)

    response = client.post(update_url(review), CHANGED, headers=HTMX)

    assert_review_alert(response, review)
    review.refresh_from_db()
    assert (review.rating, review.comment, review.edited_at) == (4, ORIGINAL, None)


def test_another_customer_gets_404_for_cancel(client, named_customer, review):
    client.force_login(named_customer)

    assert_review_alert(client.get(cancel_url(review), headers=HTMX), review)


def test_editing_a_deleted_review_is_404_with_an_alert(client, customer, review):
    client.force_login(customer)
    deleted = Review(pk=review.pk)
    review.delete()

    assert_review_alert(client.get(edit_url(deleted), headers=HTMX), deleted)
    assert_review_alert(
        client.post(update_url(deleted), CHANGED, headers=HTMX), deleted
    )


# --- Edits outlive eligibility -----------------------------------------------


def test_author_can_edit_after_their_order_is_cancelled(
    client, customer, product, delivered_order, review
):
    order = delivered_order(customer, product)
    order.status = Order.Status.CANCELLED
    order.save()
    client.force_login(customer)

    assert client.get(edit_url(review), headers=HTMX).status_code == HTTPStatus.OK
    response = client.post(update_url(review), CHANGED, headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    review.refresh_from_db()
    assert review.comment == CHANGED["comment"]


def test_author_can_edit_a_review_of_an_unavailable_product(
    client, customer, unavailable_product, make_review
):
    review = make_review(customer, unavailable_product, comment=ORIGINAL)
    client.force_login(customer)

    response = client.post(update_url(review), CHANGED, headers=HTMX)

    assert response.status_code == HTTPStatus.OK
    review.refresh_from_db()
    assert review.comment == CHANGED["comment"]


# --- Signed-out requests ------------------------------------------------------


def login_with_next(product):
    return f"{reverse('accounts:login')}?next={product.get_absolute_url()}"


def test_anonymous_htmx_update_gets_hx_redirect_to_the_product(client, review):
    response = client.post(update_url(review), CHANGED, headers=HTMX)

    assert response.status_code == HTTPStatus.NO_CONTENT
    assert response["HX-Redirect"] == login_with_next(review.product)
    review.refresh_from_db()
    assert review.comment == ORIGINAL


def test_anonymous_plain_edit_gets_the_normal_login_redirect(client, review):
    response = client.get(edit_url(review))

    assert response.status_code == HTTPStatus.FOUND
    assert response["Location"] == login_with_next(review.product)


def test_anonymous_request_for_a_missing_review_returns_to_the_catalog(client, db):
    response = client.get(reverse("reviews:edit", kwargs={"pk": 999999}), headers=HTMX)

    assert response.status_code == HTTPStatus.NO_CONTENT
    catalog = reverse("products:catalog")
    assert response["HX-Redirect"] == f"{reverse('accounts:login')}?next={catalog}"
