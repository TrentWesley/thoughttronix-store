from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("signup/", views.SignupView.as_view(), name="signup"),
    path("login/", views.SignInView.as_view(), name="login"),
    path("logout/", views.SignOutView.as_view(), name="logout"),
    path("security/", views.SecurityCenterView.as_view(), name="security"),
    path(
        "security/password/",
        views.SecurityPasswordChangeView.as_view(),
        name="password_change",
    ),
    path(
        "security/email/",
        views.EmailChangeView.as_view(),
        name="email_change",
    ),
    path(
        "password-reset/",
        views.ForgotPasswordView.as_view(),
        name="password_reset",
    ),
    path(
        "password-reset/sent/",
        views.ForgotPasswordSentView.as_view(),
        name="password_reset_done",
    ),
    path(
        "reset/complete/",
        views.ResetPasswordCompleteView.as_view(),
        name="password_reset_complete",
    ),
    path(
        "reset/<uidb64>/<token>/",
        views.ResetPasswordView.as_view(),
        name="password_reset_confirm",
    ),
]
