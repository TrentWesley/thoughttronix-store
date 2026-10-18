"""The review form, shared by create and edit, customers and staff.

The form owns the input rules: a whole-star rating from 1 to 5, and a
comment trimmed of surrounding whitespace that must then be 10–2,000
characters. Who may post, and the one-per-product rule, are enforced by
``Review.objects.eligibility`` and the database constraint.

Saving an edit records who made it (``Review.record_edit``), so pass the
signed-in user as ``editor``.
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

    def __init__(self, *args, editor=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.editor = editor

    def save(self, commit=True):
        """Save, marking an existing review as edited if anything changed."""
        if self.instance.pk and self.editor is not None and self.has_changed():
            self.instance.record_edit(self.editor)
        return super().save(commit=commit)
