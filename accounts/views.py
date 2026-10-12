from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LoginView, LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.views.generic import CreateView, FormView, TemplateView

from .forms import EmailChangeForm, SignInForm, SignupForm, StyledPasswordChangeForm


class SignupView(SuccessMessageMixin, CreateView):
    """Create a customer account, then hand off to the login page.

    New users sign in themselves — auto-login after signup is left as a
    student exercise.
    """

    form_class = SignupForm
    template_name = "accounts/signup.html"
    success_url = reverse_lazy("accounts:login")
    success_message = "Account created — you can now sign in."


class SignInView(LoginView):
    template_name = "accounts/login.html"
    authentication_form = SignInForm


class SignOutView(LogoutView):
    def post(self, request, *args, **kwargs):
        # Flash after super() has flushed the session, or the message
        # would be wiped along with it.
        response = super().post(request, *args, **kwargs)
        messages.info(request, "You have signed out.")
        return response


class SecurityCenterView(LoginRequiredMixin, TemplateView):
    """The signed-in user's account security hub.

    Always shows ``request.user`` — the template reads the context's
    ``user``, and no URL or query input selects anyone else.
    """

    template_name = "accounts/security.html"


class SecurityPasswordChangeView(LoginRequiredMixin, PasswordChangeView):
    """Change the signed-in user's password from the Security Center.

    Django's ``PasswordChangeView`` already requires sign-in, checks the
    current password, runs the validators, and calls
    ``update_session_auth_hash`` — this session stays signed in while the
    user's other sessions stop authenticating. On top of that we send the
    password-changed notification and return to the hub with a message;
    there is no separate "done" page.
    """

    form_class = StyledPasswordChangeForm
    template_name = "accounts/password_change.html"
    success_url = reverse_lazy("accounts:security")

    def form_valid(self, form):
        response = super().form_valid(form)
        self.request.user.send_password_changed_notification()
        messages.success(self.request, "Your password has been changed.")
        return response


class EmailChangeView(LoginRequiredMixin, FormView):
    """Change, or add for the first time, the signed-in user's email.

    Acts on ``request.user`` only. The change takes effect immediately;
    if there was a previous address, it gets the masked email-changed
    notice. Adding a first address sends nothing.
    """

    form_class = EmailChangeForm
    template_name = "accounts/email_change.html"
    success_url = reverse_lazy("accounts:security")

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "user": self.request.user}

    def form_valid(self, form):
        old_email = self.request.user.email
        user = form.save()
        user.send_email_changed_notice(old_email)
        messages.success(self.request, "Your email address has been updated.")
        return super().form_valid(form)
