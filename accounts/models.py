from django.contrib.auth.models import AbstractUser, UserManager
from django.db import models
from django.db.models.functions import Lower


class User(AbstractUser):
    """The store's user model.

    Roles use Django's own vocabulary and nothing else: customers are
    plain users, employees are ``is_staff``, the admin is ``is_superuser``.

    ``email`` is the account's recovery address. It stays optional, but a
    nonblank address belongs to one account only, ignoring capitalization —
    the database enforces that on its own.
    """

    # Nullable per the PRD: an absent job title is unknown, not empty.
    job_title = models.CharField(max_length=150, null=True, blank=True)  # noqa: DJ001

    class Meta(AbstractUser.Meta):
        constraints = [
            models.UniqueConstraint(
                Lower("email"),
                condition=~models.Q(email=""),
                name="accounts_user_email_ci_unique",
                violation_error_message="An account with that email address already exists.",
            ),
        ]

    @classmethod
    def normalize_recovery_email(cls, email: str | None) -> str:
        """Clean up an email a user typed, the same way everywhere.

        Trims surrounding whitespace, then applies Django's
        ``normalize_email``: the domain is lowercased and the part before
        the @ keeps the capitalization the user typed.
        """
        return UserManager.normalize_email((email or "").strip())
