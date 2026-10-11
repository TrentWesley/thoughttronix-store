# PRD: The ThoughtTronix Store — Account Security Center

*Commissioned by ThoughtTronix Product Management. "Your Thoughts, Our Business."*

---

## Problem Statement

Customers of the ThoughtTronix Store can sign up, sign in, and sign out — and that is the full extent of their control over their account. Signing up asks only for a username and a password, so the store has no way to reach a customer about their own account.

That leaves customers stuck in several situations:

- A customer who wants a stronger password has nowhere to change it while signed in.
- A customer who forgets their password has no way back in. There is no email on file and no reset flow, so the account is effectively lost.
- A customer never learns that their password or account email was changed, so if someone else gets into their account, the real owner has no warning.
- Customers who signed up through the existing signup form have no email address at all, and nothing tells them that this leaves them unable to recover their account. (The seeded demo accounts already have email addresses; the gap is in accounts created through signup.)

Employees and the store administrator use the same sign-in, and they face the same gaps for their own accounts.

## Solution

An **Account Security Center**: a signed-in page where every user manages their own account security, plus a public forgot-password flow.

- **Email at signup.** New accounts must provide an email address. Each address can belong to only one account, regardless of capitalization.
- **Security Center hub.** A page at `/accounts/security/`, reached by clicking the "Hi, {username}" greeting in the navbar. It shows the user's username and email, links to change their password or update their email, and — for accounts with no email — a reminder to add one so the account can be recovered. The reminder never blocks the user from shopping.
- **Change password.** From the hub, a signed-in user enters their current password and a new one. They stay signed in on the current device, return to the hub with a success message, and receive a notification email (if they have an email on file).
- **Update email.** From the hub, a signed-in user confirms their current password and enters a new, unique email address. It takes effect immediately. If the account had a previous address, a security notice goes to that old address, showing the new address only partially masked and telling the owner to contact ThoughtTronix support if they did not make the change.
- **Forgot password.** A "Forgot your password?" link on the sign-in page leads to a form that accepts an email address. The page always shows the same confirmation message, whether or not an account exists, so it never reveals who shops at the store. Matching active accounts with an email receive a ThoughtTronix-branded email with a single-use reset link. After setting a new password, the user sees a "reset complete" page with a link to sign in, and receives the password-changed notification.

Sign-in itself does not change: users still sign in with their username and password.

## User Stories

### Signing up with an email

1. As a visitor, I want to provide an email address when I sign up, so that the store can help me recover my account later.
2. As a visitor, I want signup to require an email address, so that every new account can be recovered.
3. As a visitor, I want to be told when the email address I entered already belongs to another account, regardless of capitalization, so that I understand why signup failed and can use a different address.
4. As a visitor, I want stray spaces around my email address to be ignored and my email's domain stored in lowercase, so that a small typing slip does not create a broken or duplicate address.
5. As a visitor, I want my email address saved with the capitalization I typed before the @, so that it appears the way I wrote it.

### Reaching the Security Center

6. As a signed-in user, I want the "Hi, {username}" greeting in the navbar to link to my Security Center, so that I can find my account security settings easily.
7. As a signed-in user, I want the Security Center to show my username and current email address, so that I can check what is on file.
8. As a signed-in user, I want the Security Center to link to separate pages for changing my password and updating my email address, so that each task is clear and focused.
9. As an existing customer without an email address, I want the Security Center to remind me to add one, so that I know my account cannot be recovered until I do.
10. As an existing customer without an email address, I want to keep using the store normally, so that the reminder never gets in the way of shopping.
11. As a staff member or administrator, I want to use the same Security Center as customers, so that I can manage my own password and email without going through the Django admin.
12. As a signed-out visitor who opens a Security Center page, I want to be sent to sign in and then returned to the page I asked for, so that I don't lose my place.
13. As a user, I want the Security Center to act only on my own account, so that nobody — including staff — can change my security settings through it.

### Changing my password

14. As a signed-in user, I want to change my password by entering my current password and a new one twice, so that only someone who knows my current password can change it.
15. As a signed-in user, I want my new password checked against the store's existing password rules, so that I don't choose a weak password.
16. As a signed-in user, I want to stay signed in on the device I'm using after changing my password, so that I don't have to sign in again immediately.
17. As a signed-in user, I want my other signed-in devices to be signed out after I change my password, so that anyone else using my old password loses access.
18. As a signed-in user, I want to return to the Security Center with a success message after changing my password, so that I know the change worked.
19. As a user with an email on file, I want to receive a notification email when my password is changed, stating the time of the change in UTC, so that I find out quickly if someone else changed it.
20. As a user, I want the password-changed notification to tell me, in plain wording, to visit the sign-in page and select "Forgot your password?" if I didn't make the change, so that I know how to regain control.
21. As a user, I want password-changed notifications never to contain my password, any reset token, or a personalized reset link, so that the email itself is safe if someone else reads it.
22. As a user without an email on file, I want my password change to succeed and show the success message even though no notification can be sent, so that missing an email never blocks a password change.

### Updating my email address

23. As a signed-in user, I want to update my email address by confirming my current password and entering a new address, so that only I can change where my account emails go.
24. As a signed-in user, I want a wrong current password to be rejected with nothing saved and no email sent, so that someone else using my signed-in session can't change my email.
25. As a signed-in user, I want a new address that belongs to another account (regardless of capitalization) to be rejected with a clear message, so that each email belongs to only one account.
26. As a signed-in user, I want re-entering my current email address, in any capitalization, to be rejected with "That's already your email address", so that I'm not told something changed when it didn't — and no notification is sent.
27. As a signed-in user, I want my new email address to be cleaned up the same way as at signup (spaces trimmed, domain lowercased, my capitalization kept before the @), so that addresses are handled consistently everywhere.
28. As a signed-in user, I want a valid email change to take effect immediately and return me to the Security Center with a success message, so that I know my new address is in use.
29. As an existing customer without an email address, I want to add one through the same update-email page, so that I can make my account recoverable.
30. As a user whose email was changed, I want a security notice sent to my previous address, so that I find out if someone else changed it.
31. As a user receiving that notice, I want it to include my username, the time of the change in UTC, and the new address partially masked (for example `s***@example.com`, or `a***@example.com` for a one-letter address), so that I can recognize my own change without the full new address being revealed to whoever reads the old inbox.
32. As a user receiving that notice, I want it to tell me to contact ThoughtTronix support immediately if I didn't make the change, so that I have a recovery path that doesn't depend on reset links now going to the new address.
33. As a user adding an email for the first time, I want no change notice to be sent, so that nobody receives a notice when there was no previous address.

### Resetting a forgotten password

34. As a signed-out customer, I want a "Forgot your password?" link on the sign-in page, so that I can start recovering my account.
35. As a customer who forgot my password, I want to enter my email address and receive a reset link, so that I can choose a new password.
36. As a customer, I want the forgot-password page to show the same confirmation message whether or not an account exists for the address I entered, so that the forgot-password page never reveals whether an account exists.
37. As a customer, I want the matching of my email address on the forgot-password page to ignore capitalization, so that typing my address in different capitals still finds my account.
38. As the store, I want accounts with no email address, inactive accounts, and accounts with unusable passwords not to receive reset links, while the page still shows the same confirmation message, so that reset emails only go to addresses that can legitimately recover an account.
39. As a customer, I want the reset email to be a friendly, ThoughtTronix Store–branded plain-text message with a working reset link, so that I trust it and can use it easily.
40. As a customer, I want reset links to expire after three days, so that old emails can't be used to take over my account indefinitely.
41. As a customer, I want each reset link to work only once and stop working as soon as my password changes, so that a leaked link can't be reused.
42. As a customer, I want my new password checked against the store's password rules during reset, so that a reset can't set a weak password.
43. As a customer who has reset my password, I want to see a "password reset complete" page with a link to sign in, so that I can sign in with my new password.
44. As a customer who has reset my password, I want not to be signed in automatically, so that a reset email alone never grants a signed-in session.
45. As a customer whose password was reset, I want to receive the same password-changed notification as for a Security Center change, without any password, reset token, or personalized reset link, so that I find out if someone else used a reset link.

### Demo and development

46. As a developer or grader, I want all existing demo accounts to keep their unique email addresses, so that password reset and notifications can be demonstrated right after seeding.
47. As a developer or grader, I want a fourth demo login — a customer with a known password and no email address — so that I can sign in and see the add-email reminder.
48. As a developer, I want every email the app sends to appear in the terminal during development, so that I can test reset links and notifications without a real mail server.
49. As a developer, I want the sender address and the support email address to be configurable through the environment, with working defaults, so that the app runs with no `.env` file present.

## Implementation Decisions

### Owning app and architecture

- All of this feature lives in the existing **accounts** app. No new app is created.
- The project's conventions apply: logic lives in models and managers, views stay thin, and every view is a class-based view.
- **No new service module is added to accounts, and no Django signals are used.** Notifications are a single-model concern, and the project keeps exactly two deliberate deep modules (order placement and dashboard queries).

### User model and database

- The existing `User` model's `email` field becomes the account's recovery address. It stays optional at the model level, so existing accounts with blank emails remain valid.
- A new **database-level unique constraint** makes email addresses unique **ignoring capitalization**, and **excludes blank emails**, so any number of accounts may have no email.
- One migration adds this constraint. It must apply cleanly to a database that already contains multiple accounts with blank emails.
- **Email normalization** is the same everywhere a customer enters an email (signup and update-email): trim leading and trailing whitespace, then apply Django's `normalize_email` behavior (lowercase the domain, keep the capitalization of the part before the @).
- **Notification methods live on `User`**: one sends the password-changed notification, and one sends the email-changed notice to a given old address. Each one renders a plain-text template, sends it with Django's mail API, and **does nothing when there is no address to send to**.
- A small **masking helper** produces the partially masked new address (first character of the part before the @, then `***`, then `@` and the full domain, for example `s***@example.com`). It handles a one-character local part (`a***@example.com`) and never returns the full address.

### Forms

- **Signup form:** extends the existing signup form to add a **required** email field. It normalizes the address and rejects one already in use (ignoring capitalization) with a friendly message. Widgets keep the existing DaisyUI input styling.
- **Password change form:** Django's stock password-change form (current password plus new password twice), validated by the project's existing password validators.
- **Update-email form:** asks for the **current password** and the **new email address**. It normalizes the address and checks that:
  - the current password is correct
  - the address is not already the user's own (ignoring capitalization), which shows **"That's already your email address"**
  - the address is not in use by another account (ignoring capitalization)

  A failure on any check saves nothing and sends nothing.
- **Password reset forms:** Django's stock reset form (email only) and set-new-password form. Django's reset form already matches emails ignoring capitalization, and sends nothing to inactive accounts or accounts with unusable passwords. Accounts with no email never match.

### Views and behavior

- **Security Center hub:** a signed-in-only page showing the user's username, their email (or the add-email reminder when blank), and links to change the password and update the email. It never blocks access to the rest of the store.
- **Password change:** a subclass of Django's `PasswordChangeView`. On success it keeps the current session signed in (Django's built-in behavior, which also signs out other sessions), calls the password-changed notification, adds a success message, and redirects to the hub. There is **no separate "password change done" page**.
- **Update email:** a signed-in-only class-based view acting on the signed-in user. On success it records the old address, saves the new one, sends the email-changed notice to the old address only if one existed, adds a success message, and redirects to the hub.
- **Password reset:** Django's built-in `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, and `PasswordResetCompleteView`, configured with accounts-namespaced success URLs and accounts templates.
  - The request page always shows the same confirmation, whether or not an account exists, has no email, is inactive, or has an unusable password. Only active accounts with a matching email and a usable password receive a reset email.
  - Reset links use Django's default `PASSWORD_RESET_TIMEOUT` of **3 days**, work only once, and stop working once the password changes (Django's token behavior).
  - Automatic sign-in after reset stays **off**. The complete page links to sign-in.
  - On a successful reset, the confirm view sends the **same password-changed notification** used by the Security Center.
- **Access control:** the hub, password-change, and update-email views require sign-in (`LoginRequiredMixin`). Signed-out visitors are redirected to sign in with a `next` parameter and returned afterward. Every signed-in user (customers, staff, and the administrator) has access. These views always act on the requesting user and never accept another user's identifier. The reset pages are public.
- **Sign-in does not change.** It remains username plus password with the existing authentication backend. No custom authentication backend is added.

### URLs

All routes are named and live under the existing `accounts` namespace. None of them contains a pk or slug.

| Path | Name | Access |
|---|---|---|
| `/accounts/security/` | `accounts:security` | Signed in |
| `/accounts/security/password/` | `accounts:password_change` | Signed in |
| `/accounts/security/email/` | `accounts:email_change` | Signed in |
| `/accounts/password-reset/` | `accounts:password_reset` | Public |
| `/accounts/password-reset/sent/` | `accounts:password_reset_done` | Public |
| `/accounts/reset/<uidb64>/<token>/` | `accounts:password_reset_confirm` | Public |
| `/accounts/reset/complete/` | `accounts:password_reset_complete` | Public |

Because Django's built-in reset views look up un-namespaced URL names by default, every success URL and the link in the reset email must explicitly use the `accounts:` names.

### Templates and UI

- All new pages live with the other accounts templates (not Django's default registration templates), extend the project's base template, and use Tailwind and DaisyUI classes only, matching the existing sign-in and signup pages. There is no JavaScript and no HTMX.
- The navbar greeting "Hi, {username}" becomes a link to the Security Center.
- The sign-in page gets a "Forgot your password?" link to the password-reset page.
- Success messages use the existing Django messages display.

### Emails

- All emails are **plain text**, rendered from templates kept with the accounts templates in an email subfolder. There are three:
  - **Password reset:** ThoughtTronix Store–branded with friendly wording. It contains a working reset link built from the `accounts:password_reset_confirm` route.
  - **Password changed** (sent after both a Security Center change and a reset): states that the password was changed and the time **labelled UTC**. If the change was unauthorized, it tells the user in plain wording to visit the sign-in page and select "Forgot your password?". It contains no clickable link, so the model method needs no request and no site-URL setting.
  - **Email changed** (sent to the old address): the username, the time **labelled UTC**, the **masked** new address, and an instruction to contact ThoughtTronix support at the configured support email immediately if the change was unauthorized. It **never** shows the full new address and **never** suggests a password reset as the recovery path.
- Neither notification email ever contains a password, a reset token, or a personalized reset link. Only the password-reset email carries a reset link.
- Times use the project's existing **UTC** time zone setting.

### Settings

- `DEFAULT_FROM_EMAIL` is read through environs from `.env`, with a default of `ThoughtTronix Store <no-reply@thoughttronix.local>`.
- A new `SUPPORT_EMAIL` setting is read through environs from `.env`, with a clearly documented development placeholder default until a real support address is configured.
- `EMAIL_BACKEND` stays Django's console backend.
- `PASSWORD_RESET_TIMEOUT` stays at Django's default (3 days).
- The app must keep running with no `.env` present.

### Seed data

- All existing demo accounts (the admin, employee, and customer logins, plus the background customers) keep their current unique email addresses unchanged.
- The seed adds a **fourth demo login**: a customer with a known, documented password and **no email address**, used to demonstrate the add-email reminder.
- The seed remains destructive and idempotent, as it is today.

### Testing

Tests use pytest and pytest-django, follow existing conventions (shared plain fixtures in the project-level conftest, no factory-boy, never invoking the seed command), and check emails via Django's in-memory test outbox. They cover working behavior and every security rule above, including:

- **Signup email:**
  - required
  - normalized
  - duplicates rejected regardless of capitalization
- **Database constraint:**
  - blocks duplicates that ignore capitalization even when the forms are bypassed
  - allows multiple blank emails
- **Access:**
  - each signed-in page redirects signed-out visitors to sign in with `next`
  - staff and the administrator can use the Security Center
  - views act only on the requesting user
- **Hub:**
  - the reminder appears only when the email is blank
  - links to both sub-pages
- **Password change:**
  - requires the correct current password and enforces the validators
  - keeps the current session signed in and redirects to the hub with a message
  - invalidates the user's other existing sessions while the current session stays authenticated
  - sends the notification only when an email exists
  - the notification labels the time UTC, gives the "Forgot your password?" instruction, and contains no password, reset token, or reset link
- **Email change:**
  - wrong password, an address used by another account, and the user's own current address in any capitalization are each rejected, with nothing saved or sent
  - a valid change saves the normalized address, redirects with a message, and sends the masked notice only to the old address
  - adding a first email sends nothing
  - the notice shows no full new address and no reset advice, and references the support email
- **Masking helper:**
  - typical addresses
  - one-character local parts
  - never returns the full address
- **Password reset:**
  - the same response for known, unknown, blank-email, inactive, and unusable-password cases
  - only the valid case sends an email, which contains a working namespaced link
  - a valid link lets the user set a new password
  - a used link can't be reused
  - completion shows the complete page with a sign-in link, does not sign the user in, and sends the password-changed notification
- **UI links:**
  - the navbar greeting links to the Security Center
  - the sign-in page links to forgot-password

### Definition of done

- `uv run pytest` passes.
- `ruff check` and `ruff format` are clean.
- The migration applies to a database that already has blank-email accounts.
- The seed produces the agreed email setup.
- The AI-usage log records the actual development sessions.

## Out of Scope

- **Recent sign-in activity** (a sign-in history page).
- **Lockout or throttling after failed sign-ins.**
- **"Sign out of all other devices"** as a separate action. Only Django's built-in sign-out of other sessions on a password change applies.
- **Email verification**, either at signup or before an email change takes effect. Email changes take effect immediately.
- **Signing in with an email address**, and any custom authentication backend.
- **Staff or admin management of other users' security settings** through this feature.
- **Blocking or forcing** existing users without an email to add one. They see a reminder only.
- **Sending a notice to the new address** on an email change. The notice goes to the old address only.
- **Automatic sign-in after a password reset.**
- **Changing the reset link lifetime** from Django's 3-day default.
- **Username recovery** ("forgot my username").
- **Real SMTP or any production email delivery.** Development uses the console backend.
- **HTML email templates.**
- **Friendly duplicate-email validation in the Django admin or `createsuperuser`.** Their behavior is unchanged, and the database constraint still prevents duplicates.
- **Rate limiting and anti-spam protection** for the password-reset form.
- **Changing the project time zone.** Times stay UTC.
- **Browser end-to-end tests** (Playwright or Selenium).

## Further Notes

- The existing signup form says on purpose that it asks for no email. That decision is reversed by this feature, and the form's documentation should be updated to match.
- The existing sign-in page and its tests stay as they are, apart from the added "Forgot your password?" link.
- Django's password reset sends links to the email on file. That is why email uniqueness is enforced at the database level, and why the email-changed notice tells the owner to contact support rather than reset their password: after a malicious change, reset links would go to the attacker's new address.
- The forgot-password page does not reveal whether an account exists. The signup and update-email forms, however, do reveal that an email is already registered when they reject a duplicate. This is an accepted trade-off of the approved friendly duplicate-email validation, and is not addressed by this feature.
- The support email default is a development placeholder. A real support address should be configured through `.env` before any real deployment.
- This PRD is the input for the implementation plan, which will be produced separately with `/prd-to-plan`.
