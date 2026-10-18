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
| `employee` | `employee123` | Staff: the back office (products, orders, reviews, dashboard)  |
| `customer` | `customer123` | A customer with order history, a live cart, and a review       |
| `noemail`  | `noemail123`  | A customer with no email on file — shows the add-email reminder |

Every login except `noemail` has a unique `<username>@example.com` email, so
password reset and the security notifications work right after seeding.

## Product reviews

Every product page has a Reviews section. Only a customer with a
**delivered** order containing the product can review it, once; authors
can edit and delete their own reviews, and staff can edit and delete any.
Everything happens in place on the product page, with no reload.

The seed adds 20 reviews, every one backed by a delivered order from its
author. Things to try:

- **Show more reviews:** the Travel Faraday Case (`/products/travel-faraday-case/`)
  has 12 reviews, so the button appears for every viewer. Two of its
  reviewers show the privacy fallbacks: "Marisol" (no last name on file)
  and "Verified customer" (no name at all).
- **Your own review:** sign in as `customer` and open MindSync. Casey's
  review is pinned at the top with Edit and Delete.
- **Write a review live:** as `customer`, open the SoulSear Authorization
  Case. Casey has a delivered order for it and no review yet, so the form
  appears. (DreamWeaver is also delivered to Casey and unreviewed.)
- **Not eligible:** as `customer`, open Seraphine Mini. That order is only
  shipped, so the page explains why there's no form.
- **Staff edit label:** Dana C.'s Seraphine review shows "Edited by
  ThoughtTronix staff."
- **Moderation:** as `employee`, open **Reviews** in the back office. Each
  row links to its review, highlighted on the product page, with the
  inline Edit and Delete controls.

The review demo data adds 13 cheap delivered orders (twelve $59 Faraday
Cases and Casey's $39 Authorization Case) and five reviewer-only customers
who can't sign in, so the dashboard's revenue moves by about $750.

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

`config/` is the project package (settings, root URLs); the six apps are
`accounts` (custom user model, sign-in, and the Account Security Center),
`products` (the public catalog and its back-office CRUD), `coupons`
(discount codes and their back-office screens), `orders` (cart, checkout,
orders — with the `place_order` service in `orders/services.py`),
`dashboard` (staff analytics, with the aggregations in
`dashboard/queries.py`), and `reviews` (product reviews, edited in place
with HTMX, and the back-office Reviews tab). Project-level templates live in `templates/`,
static sources in `assets/`. The product requirements are in `prd/`, the
phase-by-phase build plans in `plans/`, and `PROMPTS.md` is where AI usage
on this codebase gets logged.
