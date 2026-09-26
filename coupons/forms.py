"""Back-office coupon forms.

Creation sets every term; afterwards only the expiry is editable, so
the edit form is a separate one-field form. Codes are normalized
(whitespace stripped, uppercased) before the model's own validators and
uniqueness check run, so ``thoughts10`` and ``THOUGHTS10`` collide.
"""

from django import forms
from django.utils import timezone

from products.forms import StyledModelForm
from products.models import Product

from .models import Coupon, normalize_code


class CouponCodeField(forms.CharField):
    def to_python(self, value):
        return normalize_code(super().to_python(value))


class ExpiryMixin:
    """Shared expiry rule: a new or moved expiry can't already be past."""

    def clean_expires_on(self):
        expires_on = self.cleaned_data["expires_on"]
        if expires_on is not None and expires_on < timezone.localdate():
            raise forms.ValidationError(
                "Pick today or a later date — to end a coupon now, retire it."
            )
        return expires_on


EXPIRY_WIDGET = forms.DateInput(format="%Y-%m-%d", attrs={"type": "date"})


class CouponCreateForm(ExpiryMixin, StyledModelForm):
    code = CouponCodeField(
        max_length=30,
        help_text="Letters and digits; saved in uppercase. Can't be changed later.",
    )
    products = forms.ModelMultipleChoiceField(
        queryset=Product.objects.order_by("name"),
        required=False,
        help_text=Coupon._meta.get_field("products").help_text,
    )

    class Meta:
        model = Coupon
        fields = ["code", "percent_off", "products", "expires_on"]
        widgets = {"expires_on": EXPIRY_WIDGET}


class CouponExpiryForm(ExpiryMixin, StyledModelForm):
    class Meta:
        model = Coupon
        fields = ["expires_on"]
        widgets = {"expires_on": EXPIRY_WIDGET}
