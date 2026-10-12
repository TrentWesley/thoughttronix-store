from django import forms
from django.contrib.auth.forms import (
    AuthenticationForm,
    PasswordChangeForm,
    PasswordResetForm,
    SetPasswordForm,
    UserCreationForm,
)

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


class StyledPasswordChangeForm(PasswordChangeForm):
    """Django's stock password-change form, dressed in DaisyUI.

    Validation is untouched: the current password must be correct and the
    new one must pass ``AUTH_PASSWORD_VALIDATORS``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class StyledPasswordResetForm(PasswordResetForm):
    """Django's stock forgot-password form, dressed in DaisyUI.

    Matching is untouched: emails match ignoring capitalization, and only
    active accounts with a usable password receive a reset link. Accounts
    with no email never match.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class StyledSetPasswordForm(SetPasswordForm):
    """Django's stock set-new-password form, dressed in DaisyUI.

    The new password must pass ``AUTH_PASSWORD_VALIDATORS``.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"


class EmailChangeForm(forms.Form):
    """Change the signed-in user's recovery email.

    The current password must be correct. The new address is normalized
    with ``User.normalize_recovery_email`` and must be neither the user's
    own current address nor one belonging to another account, ignoring
    capitalization either way. Nothing is saved until ``save()``.
    """

    current_password = forms.CharField(
        label="Current password",
        strip=False,
        widget=forms.PasswordInput(attrs={"autocomplete": "current-password"}),
    )
    email = forms.EmailField(
        label="New email address",
        max_length=254,
        widget=forms.EmailInput(attrs={"autocomplete": "email"}),
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            field.widget.attrs["class"] = "input w-full"

    def clean_current_password(self):
        password = self.cleaned_data["current_password"]
        if not self.user.check_password(password):
            raise forms.ValidationError(
                "Your current password was entered incorrectly. Please try again."
            )
        return password

    def clean_email(self):
        email = User.normalize_recovery_email(self.cleaned_data["email"])
        if email.lower() == self.user.email.lower():
            raise forms.ValidationError("That's already your email address.")
        others = User.objects.exclude(pk=self.user.pk)
        if others.filter(email__iexact=email).exists():
            raise forms.ValidationError(
                "That email address already belongs to another account."
            )
        return email

    def save(self) -> User:
        self.user.email = self.cleaned_data["email"]
        self.user.save(update_fields=["email"])
        return self.user
