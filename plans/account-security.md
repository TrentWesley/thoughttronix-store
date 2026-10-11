# Plan: The ThoughtTronix Store — Account Security Center

> Source PRD: `prd/account-security.md`
>
> *Status: approved.* The PRD owns the requirements and this plan owns the sequence. Where a phase says "per the PRD," the PRD's wording is authoritative.

## Architectural decisions

These decisions are durable and apply to every phase:

- **Owning app**: `accounts`. No new app, no service module, and no signals. Logic lives on `User` and its manager, views are thin class-based views, and forms own their validation.
- **Model**: `accounts.User` (existing). `email` stays optional at the model level. One migration adds a database unique constraint on email that **ignores capitalization** and **excludes blank emails**. It must apply to a database that already holds several blank-email accounts.
- **Email normalization**: a single helper at the model level, on `User` or its manager. It trims whitespace, then applies Django's `normalize_email` (domain lowercased, local part kept as typed). Signup and update-email both call it. The Django admin and `createsuperuser` stay unchanged.
- **Notifications**: two methods on `User`. One sends the password-changed notification. The other sends the email-changed notice to a given old address. Both render plain-text templates from an email subfolder of the accounts templates, send with Django's mail API, and do nothing when there is no address. A small helper produces the masked address (`s***@example.com`).
- **URLs** (all in the `accounts` namespace, with no pks or slugs):

  | Path | Name | Access |
  |---|---|---|
  | `/accounts/security/` | `accounts:security` | Signed in |
  | `/accounts/security/password/` | `accounts:password_change` | Signed in |
  | `/accounts/security/email/` | `accounts:email_change` | Signed in |
  | `/accounts/password-reset/` | `accounts:password_reset` | Public |
  | `/accounts/password-reset/sent/` | `accounts:password_reset_done` | Public |
  | `/accounts/reset/<uidb64>/<token>/` | `accounts:password_reset_confirm` | Public |
  | `/accounts/reset/complete/` | `accounts:password_reset_complete` | Public |

- **Access control**: the signed-in pages use `LoginRequiredMixin` with the existing `LOGIN_URL`, so `next` round-trips. They always act on `request.user` and never take a user identifier. Customers, staff, and the administrator all have access. The reset pages are public. Sign-in itself is unchanged.
- **Settings** (environs, working defaults, runs with no `.env`):
  - `DEFAULT_FROM_EMAIL` defaults to `ThoughtTronix Store <no-reply@thoughttronix.local>`.
  - `SUPPORT_EMAIL` defaults to `support@thoughttronix.local`, documented as a development placeholder.
  - `EMAIL_BACKEND` stays the console backend.
  - `PASSWORD_RESET_TIMEOUT` stays at Django's default of 3 days.
  - `TIME_ZONE` stays UTC.
- **Templates**:
  - All pages live in `templates/accounts/`, extend `base.html`, and use Tailwind and DaisyUI only, with no JavaScript or HTMX.
  - Emails are plain text, in `templates/accounts/email/`.
  - Success messages use the existing messages display.
- **Demo data**: existing demo and background accounts keep their unique emails. A fourth login, **`noemail` / `noemail123`**, is a plain customer with no email.
- **Tests**:
  - The `accounts` tests are split into `test_*.py` modules, following the `orders/` pattern. The existing tests move over unchanged except where a phase says otherwise.
  - Shared plain fixtures go in the project `conftest.py`, including a user with an email on file. There's no factory-boy, and tests never run the seed command.
  - Emails are checked through `mail.outbox`.

**Every phase ends with the same stopping-point checklist**:

- `uv run pytest` is green.
- `uv run ruff check .` and `uv run ruff format --check .` are clean.
- The phase's manual verification has been done in the dev server.
- The phase is committed.
- Don't start the next phase until all of this is done.

---

## Phase 1: Tracer bullet — the Security Center hub

**User stories**: 6, 7, 9, 10, 11, 12, 13, 47

### What to build

The thinnest complete path through the feature: a signed-in page at `/accounts/security/` (`accounts:security`).

- It shows the requesting user's username and email.
- When the email is blank, it shows a designed add-email reminder instead. The reminder doesn't block anything.
- The navbar's "Hi, {username}" greeting becomes a link to the hub.
- Signed-out visitors are redirected to sign in with `next` and come back after signing in.
- The seed gains the `noemail` / `noemail123` customer, so the reminder can be demonstrated right away.

The links to the password and email sub-pages are added in Phases 3 and 4, once those pages exist.

Because Phase 1 opens the `accounts` test refactor, convert `accounts/tests.py` into `test_*.py` modules here, with no change in behavior.

### Acceptance criteria

- [ ] Signed-out GET of the hub redirects to `accounts:login` with `next=/accounts/security/`. Signing in through that URL lands back on the hub.
- [ ] A customer, a staff user, and a superuser can each load the hub and see their own username.
- [ ] The reminder appears only when the user's email is blank. A user with an email sees the address and no reminder.
- [ ] The hub always shows the requesting user's data, and no URL or query input selects another user.
- [ ] A user with no email can still browse the catalog and use the cart normally.
- [ ] The navbar greeting links to `accounts:security`. The existing navbar tests still pass, updated only as far as the link requires.
- [ ] The seed creates `noemail` with password `noemail123`, no email, and not staff. The seed is still destructive and idempotent, and `noemail` is included in the wipe.
- [ ] `accounts` tests are split into modules, and the full suite is green.

### Verification

Run `seed` and `tailwind runserver`. Sign in as `noemail` and click the greeting to see the reminder. Sign in as `customer` to see the email. Visit `/accounts/security/` while signed out to confirm the `next` round-trip.

### Stopping point

The hub is live and demoable with both an emailed account and an email-less one. No forms exist yet.

---

## Phase 2: Unique emails, and signup asks for one

**User stories**: 1, 2, 3, 4, 5

### What to build

Make email the account's recovery identity:

- Add the case-insensitive, blank-excluding unique constraint on `User.email`, in one migration.
- **Before applying that migration to any existing database** (the dev database and the committed snapshot), check it for nonblank emails that are duplicates when capitalization is ignored. If any exist, **stop and report them** to the user: the usernames and the colliding addresses. Don't write a data migration, edit or blank any email, or delete any account to make the migration pass. Phase 2 stays open until the user decides how to resolve them.
- Add the model-level normalization helper (trim, then `normalize_email`).
- Extend the signup form with a **required** email field. It normalizes the address and rejects one already in use, regardless of capitalization, with a friendly message. The field keeps the DaisyUI `input w-full` styling.
- Update the signup form's docstring, which currently says "No email" on purpose, to match.
- Update the signup template if it needs to render the new field.

### Acceptance criteria

- [ ] Each existing database was checked for duplicate nonblank emails (ignoring capitalization) before the migration was applied. Either none were found, or they were reported and the user resolved them. No user data was changed silently.
- [ ] The migration applies cleanly to a database with several blank-email accounts, verified against a freshly seeded database.
- [ ] Bypassing forms, two users whose emails differ only in case can't both be saved. The database raises `IntegrityError`.
- [ ] Several users with blank emails can coexist.
- [ ] Signup without an email fails with a field error, and no user is created.
- [ ] Signup with `  Sam@Example.COM  ` stores `Sam@example.com`.
- [ ] Signup with an email already used under different capitalization fails with a friendly field error.
- [ ] The existing signup happy-path test now posts an email and still lands on sign-in with "Account created".
- [ ] The normalization helper has unit tests for trimming, lowercasing the domain, and keeping the local part's case.

### Verification

Run the duplicate-email check against the existing dev database and the committed snapshot, and stop if it finds anything. Then run `migrate` against the existing dev database before re-seeding. Sign up through the UI with a mixed-case, padded email, then try a case-variant duplicate.

### Stopping point

Every new account has a unique, normalized email, and the database enforces uniqueness on its own.

---

## Phase 3: Change password, with notification

**User stories**: 8 (password link), 14, 15, 16, 17, 18, 19, 20, 21, 22, 48, 49 (`DEFAULT_FROM_EMAIL`)

### What to build

Add a password-change page at `/accounts/security/password/` (`accounts:password_change`). It subclasses `PasswordChangeView` with Django's stock form and the project's validators. On success:

- the current session stays signed in, and Django's built-in behavior signs out the user's other sessions
- the user's password-changed notification is sent
- a success message is added
- the user is redirected to the hub

There is no separate "done" page.

The password-changed notification method on `User` renders a plain-text template. The template states the change and its time labelled **UTC**. It tells the user, in plain words, to visit the sign-in page and select "Forgot your password?" if they didn't make the change. It contains no link, password, or token, and it is a no-op when the user has no email.

`DEFAULT_FROM_EMAIL` moves into settings via environs with the PRD's default, and it is added to `.env.example`. The hub gains its "Change password" link.

### Acceptance criteria

- [ ] Signed-out access redirects to sign in with `next`.
- [ ] A wrong current password or a validator-failing new password re-renders with errors. The password is unchanged and no email is sent.
- [ ] A valid change redirects to the hub with a success message, and the client is still authenticated afterward.
- [ ] A second session for the same user, made with another client before the change, is no longer authenticated after it.
- [ ] A user with an email gets exactly one message from `DEFAULT_FROM_EMAIL`. Its body contains "UTC" and "Forgot your password?", and contains no password, no reset-token-shaped string, and no `http`.
- [ ] A user with no email changes their password successfully, sees the message, and `mail.outbox` stays empty.
- [ ] The hub links to `accounts:password_change`.
- [ ] Staff and superuser can use the page.

### Verification

Change `customer`'s password in the dev server and read the notification printed to the console. Repeat as `noemail` and confirm the change succeeds with no console email.

### Stopping point

Signed-in users can rotate their password safely and are notified when they do.

---

## Phase 4: Update email, with masked notice

**User stories**: 8 (email link), 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 49 (`SUPPORT_EMAIL`)

### What to build

Add an update-email page at `/accounts/security/email/` (`accounts:email_change`). It's a signed-in class-based view acting on `request.user`, with a form that asks for the current password and the new email. The form:

- normalizes the address with the Phase 2 helper
- rejects a wrong password
- rejects the user's own current address in any capitalization with **"That's already your email address"**
- rejects an address used by another account

On success the view records the old address, saves the new one, and sends the email-changed notice to the old address only if one existed. It then adds a success message and redirects to the hub. The same page is how an email-less user adds a first address.

Add the masking helper, with first character + `***` + `@domain` and correct handling of one-character local parts.

The email-changed notice method on `User` renders a plain-text template containing:

- the username
- the time labelled **UTC**
- the masked new address
- an instruction to contact ThoughtTronix support at `SUPPORT_EMAIL` immediately if the change wasn't theirs

It never shows the full new address and never suggests a password reset.

`SUPPORT_EMAIL` is added via environs with the default `support@thoughttronix.local`, documented as a placeholder in `.env.example`. The hub gains its "Update email" link. For an email-less user, the reminder points to this page.

### Acceptance criteria

- [ ] Signed-out access redirects to sign in with `next`.
- [ ] A wrong password, an address used by another account (any case), and the user's own address (any case, with the exact message above) are each rejected. The stored email is unchanged and `mail.outbox` is empty.
- [ ] A valid change stores the normalized address, redirects to the hub with a success message, and sends exactly one notice, addressed only to the old address.
- [ ] The notice contains the username, "UTC", the masked address, and the `SUPPORT_EMAIL` value. It does not contain the full new address, the word "reset", or "Forgot your password".
- [ ] Adding a first email (old address blank) saves and sends nothing.
- [ ] The masking helper is unit-tested on `sam@example.com` → `s***@example.com` and `a@example.com` → `a***@example.com`, and never returns its input unchanged.
- [ ] The hub links to `accounts:email_change`, and the reminder links there for email-less users.
- [ ] Staff and superuser can use the page.

### Verification

As `customer`, change the email and read the masked notice in the console. As `noemail`, add an email, confirm the reminder disappears from the hub, and confirm no console email was sent. Try re-entering the current address in upper case.

### Stopping point

Users fully control their recovery address, and the old inbox is warned about every change.

---

## Phase 5: Forgot password

**User stories**: 34, 35, 36, 37, 38, 39, 40, 41, 42, 43, 44, 45

### What to build

The public reset flow uses Django's `PasswordResetView`, `PasswordResetDoneView`, `PasswordResetConfirmView`, and `PasswordResetCompleteView` at the four PRD paths.

- Each is configured with the `accounts:` success URLs and with templates in `templates/accounts/`. The emails go in `templates/accounts/email/`.
- The reset email is a plain-text, ThoughtTronix Store-branded message. Its link is built from `accounts:password_reset_confirm`.
- Automatic sign-in after reset stays off.
- On a successful reset, the confirm view sends the same password-changed notification as Phase 3.
- The sign-in page gains a "Forgot your password?" link. The complete page links to sign-in.

### Acceptance criteria

- [ ] The sign-in page links to `accounts:password_reset`.
- [ ] Each case below redirects to `accounts:password_reset_done` and shows the same confirmation:
  - a known email
  - a case-variant of a known email
  - an unknown email
  - an address submitted while blank-email accounts exist, which matches none of them
  - an inactive account
  - an unusable-password account
- [ ] Only the known and case-variant cases send an email.
- [ ] The reset email is branded and contains a URL that resolves to `accounts:password_reset_confirm`. Following it lets the user set a new password that passes the validators. A weak password is rejected.
- [ ] After completion, the complete page renders with a link to `accounts:login`, the client is not authenticated, and the user can sign in with the new password.
- [ ] Completion sends the password-changed notification, which has no link or token.
- [ ] Reusing the same reset link afterward shows the invalid-link state and can't change the password.
- [ ] No code overrides `PASSWORD_RESET_TIMEOUT`, so the 3-day default holds.

### Verification

Sign out, click "Forgot your password?", and enter `CUSTOMER@example.com`. Copy the console link, reset the password, see the complete page, and sign in with the new password. Revisit the old link to confirm it's dead. Submit an unknown address and confirm the page is identical and nothing is printed.

### Stopping point

Any customer with an email on file can recover their account without staff help.

---

## Phase 6: Demo world and definition of done

**User stories**: 46, 47 (documentation)

### What to build

This phase closes the feature out against the PRD's definition of done.

- Confirm the seed leaves every existing demo and background account's email unchanged, and that `noemail` has none.
- Add `noemail / noemail123` to the README's demo-login table and to the seed docstring.
- Document `DEFAULT_FROM_EMAIL` and `SUPPORT_EMAIL` in `.env.example` and the README.
- Update CLAUDE.md to document the Account Security Center architecture. The `accounts/` layout entry should cover the Security Center, the forgot-password flow, the case-insensitive unique recovery email, normalization on the model level, and the two notification methods on `User`. It should also note that there is no service module and no signals, and list the new `accounts:` routes. The new routes are `security`, `password_change`, `email_change`, `password_reset`, `password_reset_done`, `password_reset_confirm`, and `password_reset_complete`.
- Do an end-to-end manual pass of every flow with the console backend.
- Append the PROMPTS.md entries for the actual sessions.

### Acceptance criteria

- [ ] `migrate` from the pre-feature schema on a seeded database succeeds, and re-running `seed` afterward succeeds twice in a row.
- [ ] After seeding, `admin`, `employee`, `customer`, and every background customer keep their prior emails, and `noemail` has a blank email.
- [ ] The README and seed docstring list all four demo logins.
- [ ] CLAUDE.md describes the Account Security Center's architecture and lists its `accounts:` routes. Nothing in it still describes signup as email-free.
- [ ] The app starts and every new page renders with no `.env` present.
- [ ] `uv run pytest`, `uv run ruff check .`, and `uv run ruff format --check .` are all clean.
- [ ] PROMPTS.md has entries appended for this feature's sessions, with no existing history rewritten.

### Verification

Rename `.env` away if one exists, then run `seed` and `runserver`. Walk all four demo logins through the hub, and complete one reset round-trip.

### Stopping point

The Account Security Center is complete, documented, and graded-demo ready.
