# The ThoughtTronix Store

*Your Thoughts, Our Business.*

A server-rendered Django 6 storefront and back office for the world's most
beloved consumer neural technology: browse the catalog, fill a cart, check
out through a fully validated form, and — if you're staff — run the store
from the back office, analytics dashboard included.

## Getting started

Requires Python 3.13 and [uv](https://docs.astral.sh/uv/). No Node.js —
Tailwind runs as a standalone binary.

```bash
uv sync
uv run python manage.py migrate
uv run python manage.py seed
uv run python manage.py tailwind runserver
```

Then open <http://127.0.0.1:8000/>. From clone to browsing the store, this
takes about two minutes.

## Demo logins

The `seed` command creates a fixed demo world — the same one every run:

| Username   | Password      | Who they are                                                  |
| ---------- | ------------- | ------------------------------------------------------------- |
| `admin`    | `admin123`    | Superuser: everything below, plus the Django admin at `/admin/` |
| `employee` | `employee123` | Staff: the back office (products, orders, dashboard)           |
| `customer` | `customer123` | A customer with order history and a live cart                  |
| `noemail`  | `noemail123`  | A customer with no email on file — shows the add-email reminder |

Every login except `noemail` has a unique `<username>@example.com` email, so
password reset and the security notifications work right after seeding.

## Account Security Center

Click **Hi, {username}** in the navbar (or visit `/accounts/security/`) to
reach the Security Center. Every signed-in user — customer, employee, or
admin — can review their username and email, change their password, and add
or update their recovery email. Signed-out users can recover their account
from **Forgot your password?** on the sign-in page.

| Path                                | What it does                                              |
| ----------------------------------- | --------------------------------------------------------- |
| `/accounts/security/`               | The hub (signed in)                                       |
| `/accounts/security/password/`      | Change password; notifies the address on file             |
| `/accounts/security/email/`         | Add or update the email; a masked notice goes to the old address |
| `/accounts/password-reset/`         | Forgot password — always shows the same confirmation      |
| `/accounts/reset/<uidb64>/<token>/` | Choose a new password from the emailed link (single use, 3 days) |

There is no real mail server: every email the app sends is **printed in the
terminal running the dev server**. To try a reset, sign out, select
"Forgot your password?", enter `customer@example.com`, and open the link
printed in the console.

The console shows each email exactly as it would be sent. Emails with lines
longer than 78 characters — all three of the store's emails — are
quoted-printable encoded, so long lines wrap with a trailing `=` (and an em
dash appears as `=E2=80=94`). The reset link always wraps: delete the
`=` at the end of its first line and join it to the next line before
pasting it into the browser.

## Configuration

The app runs with no `.env` file. To override a default, copy `.env.example`
to `.env` and uncomment the line:

| Setting              | Default                                              | Purpose                                           |
| -------------------- | ---------------------------------------------------- | ------------------------------------------------- |
| `SECRET_KEY`         | an insecure development key                          | Django's secret key                               |
| `DEBUG`              | `True`                                               | Debug mode                                        |
| `ALLOWED_HOSTS`      | `localhost,127.0.0.1`                                | Hosts Django will serve                           |
| `DEFAULT_FROM_EMAIL` | `ThoughtTronix Store <no-reply@thoughttronix.local>` | Sender on every email                             |
| `SUPPORT_EMAIL`      | `support@thoughttronix.local`                        | Contact named in the email-changed notice — a development placeholder; set a real address before any real deployment |

## Commands

| Command                                     | What it does                             |
| ------------------------------------------- | ---------------------------------------- |
| `uv sync`                                    | Install dependencies                     |
| `uv run python manage.py migrate`            | Apply database migrations                |
| `uv run python manage.py seed`               | Reset the database to the demo world (destructive, idempotent) |
| `uv run python manage.py tailwind runserver` | Dev server + Tailwind watch              |
| `uv run python manage.py tailwind build`     | Compile production CSS                   |
| `uv run pytest`                              | Run the test suite                       |
| `uv run ruff check .`                        | Lint                                     |
| `uv run ruff format .`                       | Format                                   |

## Repo layout

`config/` is the project package (settings, root URLs); the five apps are
`accounts` (custom user model, sign-in, and the Account Security Center),
`products` (the public catalog and its back-office CRUD), `coupons`
(discount codes and their back-office screens), `orders` (cart, checkout,
orders — with the `place_order` service in `orders/services.py`), and
`dashboard` (staff analytics, with the aggregations in
`dashboard/queries.py`). Project-level templates live in `templates/`,
static sources in `assets/`. The product requirements are in `prd/`, the
phase-by-phase build plans in `plans/`, and `PROMPTS.md` is where AI usage
on this codebase gets logged.
