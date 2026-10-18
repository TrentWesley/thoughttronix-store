"""The review form: a 1–5 star rating and a trimmed 10–2,000 character comment."""

import pytest

from .forms import ReviewForm

# ModelForm validation checks the rating constraint with a database query.
pytestmark = pytest.mark.django_db


def form_with(**data):
    return ReviewForm(
        data={"rating": "4", "comment": "A perfectly reasonable hub.", **data}
    )


def test_a_rating_and_comment_are_valid():
    form = form_with()

    assert form.is_valid(), form.errors
    assert form.cleaned_data == {"rating": 4, "comment": "A perfectly reasonable hub."}


def test_the_form_exposes_only_rating_and_comment():
    assert list(ReviewForm().fields) == ["rating", "comment"]


def test_rating_is_required():
    form = form_with(rating="")

    assert not form.is_valid()
    assert "rating" in form.errors


@pytest.mark.parametrize("rating", ["0", "6", "4.5", "five"])
def test_rating_must_be_a_whole_star_from_one_to_five(rating):
    form = form_with(rating=rating)

    assert not form.is_valid()
    assert "rating" in form.errors


@pytest.mark.parametrize("rating", ["1", "2", "3", "4", "5"])
def test_every_whole_star_is_accepted(rating):
    form = form_with(rating=rating)

    assert form.is_valid(), form.errors
    assert form.cleaned_data["rating"] == int(rating)


def test_comment_is_required():
    form = form_with(comment="")

    assert not form.is_valid()
    assert "comment" in form.errors


def test_comment_is_trimmed():
    form = form_with(comment="   She hears everything.  \n\t")

    assert form.is_valid(), form.errors
    assert form.cleaned_data["comment"] == "She hears everything."


def test_whitespace_only_comment_is_rejected():
    form = form_with(comment=" \n\t" * 10)

    assert not form.is_valid()
    assert "comment" in form.errors


@pytest.mark.parametrize(
    ("length", "valid"), [(9, False), (10, True), (2000, True), (2001, False)]
)
def test_comment_length_limits(length, valid):
    form = form_with(comment="x" * length)

    assert form.is_valid() is valid
    assert ("comment" in form.errors) is not valid


def test_length_is_measured_after_trimming():
    form = form_with(comment="    " + "x" * 9 + "    ")

    assert not form.is_valid()
    assert "comment" in form.errors
