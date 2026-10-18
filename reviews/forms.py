"""The review form, shared by create and (later) edit, customers and staff.

The form owns the input rules: a whole-star rating from 1 to 5, and a
comment trimmed of surrounding whitespace that must then be 10–2,000
characters. Who may post, and the one-per-product rule, are enforced by
``Review.objects.eligibility`` and the database constraint.
"""

from django import forms

from .models import COMMENT_MAX_LENGTH, COMMENT_MIN_LENGTH, Review


class ReviewForm(forms.ModelForm):
    rating = forms.TypedChoiceField(
        label="Rating",
        choices=Review.Rating.choices,
        coerce=int,
        widget=forms.RadioSelect,
    )
    # CharField strips by default, so whitespace-only comes back empty and
    # fails ``required``, and the lengths are measured after trimming.
    comment = forms.CharField(
        label="Your review",
        min_length=COMMENT_MIN_LENGTH,
        max_length=COMMENT_MAX_LENGTH,
        widget=forms.Textarea(
            attrs={
                "class": "textarea w-full",
                "rows": 4,
                "placeholder": "What was it like to live with?",
            }
        ),
    )

    class Meta:
        model = Review
        fields = ["rating", "comment"]
