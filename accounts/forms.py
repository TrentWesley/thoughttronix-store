from django import forms
from django.contrib.auth.forms import AuthenticationForm, UserCreationForm

from .models import User


class SignupForm(UserCreationForm):
    """Django's stock signup fields plus a required recovery email.

    The email is normalized with ``User.normalize_recovery_email`` and must
    not already belong to another account, ignoring capitalization. The
    widgets carry DaisyUI classes because plain Django forms own their own
    styling here.
    """

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Optional on the model so older accounts stay valid; required here.
        self.fields["email"].required = True
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"

    def clean_email(self):
        email = User.normalize_recovery_email(self.cleaned_data["email"])
        if User.objects.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "That email address already belongs to another account."
            )
        return email


class SignInForm(AuthenticationForm):
    """The stock authentication form, dressed in DaisyUI."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"
