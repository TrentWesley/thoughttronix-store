# Plan: The ThoughtTronix Store — Product Reviews

> Source PRD: `prd/product-reviews.md`
>
> *Status: approved breakdown.* The PRD owns the requirements and this plan owns the sequence. Where a phase says "per the PRD," the PRD's wording is authoritative.

## Architectural decisions

These decisions are durable and apply to every phase:

- **Owning app**: a new **`reviews`** app, added to `INSTALLED_APPS` and described in CLAUDE.md. It owns the model, manager, forms, views, URLs, templates, partials, and tests.
  - Dependencies point one way: **reviews depends on products and orders**. Those two apps never import reviews. The only exceptions are that the product detail page includes the Reviews section, and the product delete confirmation shows a review count.
  - **No service module and no signals.** Logic lives in the model and its `ReviewQuerySet`/manager, views are thin class-based views, and forms own their validation.
- **Model**: `Review`
  - `user`: FK to `accounts.User`, cascade on delete
  - `product`: FK to `products.Product`, cascade on delete
  - `rating`: small positive integer, whole-star choices 1–5, required
  - `comment`: text, required, with model validators for a minimum of 10 and a maximum of 2,000 characters
  - `created_at`: defaults to now and isn't auto-set, so tests and the seed can backdate reviews
  - `updated_at`: `auto_now`, kept for bookkeeping only
  - `edited_at`: nullable. It drives the "Edited" label.
  - `edited_by_staff_at`: nullable. It's set when someone other than the author edits the review, and cleared when the author edits it.
  - Constraints: **unique (user, product)** and a **check constraint keeping rating between 1 and 5**.
- **Rules live in two places only**:
  - **Delivered orders**: an `Order` queryset method in `orders` returns the user's `DELIVERED` orders containing a given product. `PLACED`, `SHIPPED`, and `CANCELLED` don't count.
  - **Everything else**: `ReviewQuerySet`/manager. That covers eligibility for (user, product), which returns whether the user may review and, if not, why: *signed out*, *no delivered purchase*, or *already reviewed*. It also covers the live `Avg`/`Count` summary, and newest-first listing that excludes given (pinned) reviews.
  - Eligibility is checked **at creation only**. It ignores product availability, and staff get no exemption.
- **Public display name**: a method or property on `Review` that returns "Margaret W.", "Margaret", or "Verified customer". It never returns a username, email address, or full last name.
- **URLs**: all named in the `reviews:` namespace, with pks for review actions. The public product page keeps its slug URL (`/products/<slug>/`).

  | Path (indicative) | Name | Method | Access |
  |---|---|---|---|
  | `/reviews/product/<pk>/create/` | `reviews:create` | POST | Signed in + eligible |
  | `/reviews/product/<pk>/more/` | `reviews:more` | GET | Public |
  | `/reviews/<pk>/edit/` | `reviews:edit` | GET | Author or staff |
  | `/reviews/<pk>/update/` | `reviews:update` | POST | Author or staff |
  | `/reviews/<pk>/cancel-edit/` | `reviews:cancel_edit` | GET | Author or staff |
  | `/reviews/<pk>/delete/` | `reviews:delete_confirm` | GET | Author or staff |
  | `/reviews/<pk>/delete/confirm/` | `reviews:delete` | POST | Author or staff |
  | `/reviews/<pk>/cancel-delete/` | `reviews:cancel_delete` | GET | Author or staff |
  | `/backoffice/reviews/` | `reviews:manage_reviews` | GET | Staff |

  The exact path strings may change during implementation. The namespace, the URL names' meanings, the use of pks, and the `/backoffice/` area for the list are fixed.
- **Access control**:
  - **Ownership is enforced by the lookup**, as in the cart. Customers fetch only from their own reviews, and staff fetch from all reviews. Anything else is a **404**, for the GET endpoints as well as the POSTs.
  - An ineligible create is a **403** and saves nothing. Every state change is a POST.
  - The back-office list uses the existing `StaffRequiredMixin` and a `section` context entry.
- **HTMX conventions**:
  - Every review endpoint returns a partial from `templates/reviews/partials/_<name>.html`. Partials never extend `base.html`.
  - The summary refreshes as an out-of-band swap.
  - Each review card has a stable anchor id built from its pk (`review-<pk>`).
  - Errors: 403 and 404 responses keep their real status codes and return an inline DaisyUI alert, aimed at the affected element with `HX-Retarget` and `HX-Reswap`.
  - Only the product page carries an `htmx-config` meta tag, via a new empty head block in `base.html`. Its `responseHandling` rules are: 204 no swap; 2xx/3xx swap; 403/404 swap as errors; other 4xx/5xx no swap.
  - An anonymous HTMX request gets `HX-Redirect` to `accounts:login` with `next` set to the product page. A non-HTMX anonymous request gets the normal login redirect.
  - Double submits are blocked with `hx-disabled-elt`. There's no JavaScript beyond HTMX attributes and configuration, and no new dependencies.
- **Templates**: Tailwind + DaisyUI only, `night` theme. The Reviews section sits below the product information on `products/detail.html`. Comments are autoescaped, with line breaks preserved.
- **Tests**:
  - pytest + pytest-django, in `reviews/test_*.py` modules, following the `orders/` pattern.
  - Shared plain fixtures go in the project `conftest.py`, including a delivered-order helper. No factory-boy.
  - Tests **never run the seed command**.

### Every phase follows the same workflow

1. **RED.** Write the phase's tests first, from its acceptance criteria. Run `uv run pytest` and confirm the new tests **fail for the expected reason**, not because of import errors or typos. Show the failing output.
2. **GREEN.** Write the least implementation that makes the tests pass. Refactor only while the tests stay green.
3. **Automated checks.** All three must be clean:
   - `uv run pytest`: the whole suite, not just the new tests
   - `uv run ruff check .`
   - `uv run ruff format --check .`
   - `uv run python manage.py makemigrations --check --dry-run` when the phase touches models
4. **Manual browser verification.** Run the phase's checklist against `uv run python manage.py tailwind runserver` in a real browser, and report what was observed.
5. **Stop for approval.** Present the results and wait for the user's explicit approval. **Don't commit or start the next phase without it.**
6. **Commit and push.** After approval, commit the phase (message `Complete Product Reviews Phase N`, matching the existing history), push to `origin`, and append the session to `PROMPTS.md`.

---

## Phase 1: Tracer bullet — reviews appear on the product page

**User stories**: 1, 2, 3, 4, 5, 6, 9, 10, 13, 14, 15, 58, 62, 63

### What to build

The thinnest complete path through every layer:

- Create the `reviews` app, the `Review` model, and its migration and constraints.
- Register `Review` in the Django admin.
- Add the public display name and the queryset's summary and newest-first listing.
- Give every product page, including unavailable ones, a read-only **Reviews section** for signed-in and signed-out visitors alike. It shows:
  - the summary: average stars and review count, or "No reviews yet" when there are none
  - the review cards, newest first. Each card has stars, the autoescaped comment, the display name, the posted date, a **Verified purchase** badge, and a stable `review-<pk>` anchor.

In this phase, reviews exist only through fixtures and the admin. There's no form yet, and no pagination; that comes in Phase 5.

### Acceptance criteria

- [ ] RED tests were written first and failed for the expected reason before implementation.
- [ ] Constraints: the database rejects a second review for the same (user, product), and rejects ratings of 0 and 6.
- [ ] Comment length: model validation rejects 9 and 2,001 characters, and accepts 10 and 2,000.
- [ ] Cascades: deleting a product deletes its reviews, and deleting a user deletes theirs. An order line's product still becomes empty when its product is deleted.
- [ ] Display name: "Margaret W." with both names, "Margaret" with no last name, and "Verified customer" with no first name. Public pages never show usernames or email addresses.
- [ ] The summary shows the correct average and count, and "No reviews yet" when the product has no reviews.
- [ ] Reviews are listed newest first, each with a Verified purchase badge. Comments are autoescaped: an injected `<script>` appears as text.
- [ ] Reviews of an unavailable product are readable while signed out.
- [ ] `Review` is in the admin.
- [ ] Browser: product pages with and without reviews (added through the admin) look right in the `night` theme.
- [ ] Checks green, approval received, committed and pushed.

---

## Phase 2: Writing a review in place — eligibility, form, creation, and HTMX error handling

**User stories**: 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32, 33, 34, 35, 59, 60

### What to build

The full create path end to end, plus the HTMX error machinery that later phases reuse.

**Eligibility and the form slot**
- Add the `Order` delivered-with-product queryset method and the `ReviewQuerySet` eligibility check.
- The product page's **form slot** renders one of four states:
  - **signed out**: a "Sign in to review products you've purchased" link with `next` set to the product
  - **no delivered purchase**: a short not-eligible message
  - **eligible**: the review form
  - **already reviewed**: the user's own review, pinned at the top of the list and excluded from the general list so it appears only once

**The form**
- Rating uses DaisyUI rating stars (radio inputs, required, 1–5). The comment is trimmed, must not be blank or whitespace only, and must be 10–2,000 characters.

**Create endpoint**
- An HTMX POST to `reviews:create`. The server re-checks eligibility.
- **Success**: returns the pinned own-review card plus the summary as an out-of-band swap.
- **Invalid input**: re-renders the form with field errors and keeps what the user typed (200).
- **Duplicate race**: the save runs in a nested atomic block. If the unique constraint raises an integrity error, it's caught and the response shows the existing review with a friendly notice (200).
- The submit button uses `hx-disabled-elt`.

**Error handling, built once here for reuse in later phases**
- Add an empty head block in `base.html`, filled with the `htmx-config` meta tag **on the product page only**.
- Add an inline alert partial.
- Add a reusable way for review views to return 403 or 404 with the alert, `HX-Retarget`, `HX-Reswap`, and a refreshed summary where relevant.
- Add `HX-Redirect` to sign-in (with `next` set to the product) for anonymous HTMX requests. Non-HTMX requests get the normal login redirect.

### Acceptance criteria

- [ ] RED tests were written first and failed for the expected reason before implementation.
- [ ] Eligibility:
  - [ ] `DELIVERED` qualifies. `PLACED`, `SHIPPED`, and `CANCELLED` each don't.
  - [ ] Signed out is refused, and so is already reviewed.
  - [ ] **Next of kin** is refused: a user with no order of their own is refused even when a relative has a delivered order.
  - [ ] A verified purchaser can review an **unavailable** product.
  - [ ] Staff without a qualifying purchase are refused.
- [ ] The form slot shows the right state for each case: sign-in link (with the right `next`), not-eligible message, form, or the user's own pinned review.
- [ ] Form validation:
  - [ ] Rating is required and must be 1–5.
  - [ ] The comment is trimmed, and whitespace-only is rejected.
  - [ ] 9 characters is rejected, 10 accepted, 2,000 accepted, and 2,001 rejected.
- [ ] Create:
  - [ ] Success returns the own-review card partial plus the summary as an out-of-band swap.
  - [ ] Invalid input returns 200 with field errors and the typed values preserved.
  - [ ] An ineligible create returns **403** with the alert partial and the `HX-Retarget`/`HX-Reswap` headers, and saves nothing.
  - [ ] A duplicate caught by the database constraint returns the existing review with a notice. There's no 500, and exactly one review exists.
- [ ] The `htmx-config` meta tag is on the product page and **not** on other pages, such as the catalog and the cart.
- [ ] An anonymous HTMX POST gets `HX-Redirect` to sign-in with `next` set to the product page. A non-HTMX anonymous POST gets the normal redirect.
- [ ] Browser:
  - [ ] Posting a review has no page reload, the scroll position holds, the summary updates, and the button disables during the request.
  - [ ] Field errors appear inline.
  - [ ] Signing out in another tab, then submitting, lands on sign-in and returns to the product afterward.
  - [ ] HTMX 2 picks up the page-scoped config: a forced 403 visibly swaps in the alert.
- [ ] Checks green, approval received, committed and pushed.

---

## Phase 3: Editing in place, with edit tracking

**User stories**: 11, 12, 36, 37, 38, 39, 40, 41, 46, 47, 48, 49, 61

### What to build

- An **Edit** button on a card, shown only to the author and to staff, swaps the card for the same review form in place (`reviews:edit`).
- **Save** (`reviews:update`) updates the review and returns the card plus the refreshed summary out of band. **Cancel** (`reviews:cancel_edit`) restores the card unchanged.
- The save path, in the form or the model and not the view, records edits:
  - every edit sets `edited_at`
  - an edit by someone other than the author sets `edited_by_staff_at`
  - an author edit, including a staff member editing their own review, clears it
- Cards show **"Edited"** and **"Edited by ThoughtTronix staff"** when those fields are set.
- Ownership is enforced by the lookup. A failed lookup returns a 404 through the Phase 2 error machinery.
- Editing depends only on authorship or staff status. It doesn't depend on eligibility, so a review survives its order being cancelled, and its author can still edit it.

### Acceptance criteria

- [ ] RED tests were written first and failed for the expected reason before implementation.
- [ ] Edit, update, and cancel return the right partials. The update includes the summary as an out-of-band swap. Invalid input returns 200 with field errors.
- [ ] Edit tracking:
  - [ ] A new review has no "Edited" label.
  - [ ] A customer edit sets `edited_at` only.
  - [ ] A staff edit of another user's review sets `edited_by_staff_at`.
  - [ ] A staff edit of their own review doesn't.
  - [ ] An author edit clears `edited_by_staff_at`.
- [ ] Permissions:
  - [ ] Authors and staff can edit.
  - [ ] Another customer gets **404** (with the alert and `HX-Retarget`/`HX-Reswap`) for both the edit form and the update, and the data is unchanged.
  - [ ] There are no Edit buttons on other customers' reviews.
- [ ] After the review's order is cancelled, its author can still edit it.
- [ ] Browser:
  - [ ] Edit, Save, and Cancel happen in place with no reload, and the summary updates after a rating change.
  - [ ] The staff label appears after a staff edit and disappears after the author edits again.
  - [ ] Editing a review deleted in another tab shows "This review is no longer available."
- [ ] Checks green, approval received, committed and pushed.

---

## Phase 4: Deleting in place

**User stories**: 42, 43, 44, 45, 50

### What to build

- **Delete** on a card, shown only to the author and to staff, makes a GET (`reviews:delete_confirm`) that changes nothing. It swaps the card for a DaisyUI inline confirmation: "Delete this review? This can't be undone." with **Confirm Delete** and **Cancel**.
- **Confirm Delete** (`reviews:delete`, POST) removes the review, removes the card, and refreshes the summary out of band.
- When the author deletes their own review, the form slot also re-renders based on their current eligibility.
- **Cancel** (`reviews:cancel_delete`) restores the card.
- Ownership is enforced by the lookup, with 404s going through the Phase 2 error machinery.

### Acceptance criteria

- [ ] RED tests were written first and failed for the expected reason before implementation.
- [ ] The confirmation GET returns the confirmation partial and changes nothing. Cancel returns the unchanged card.
- [ ] Confirm Delete removes the review and returns the summary as an out-of-band swap.
- [ ] Authors and staff can delete. Another customer gets **404** (with the alert and headers) for both the confirmation and the delete, and the review still exists.
- [ ] Slot after delete:
  - [ ] The author sees the form again when they still have a delivered order.
  - [ ] The author sees the not-eligible message when that order has since been cancelled.
- [ ] A review whose order was cancelled can still be deleted by its author.
- [ ] Browser:
  - [ ] Confirm and Cancel work in place with no reload, and the scroll position holds.
  - [ ] The summary updates.
  - [ ] The form reappears in the slot after the author deletes their own review.
- [ ] Checks green, approval received, committed and pushed.

---

## Phase 5: Show more reviews

**User stories**: 7, 8

### What to build

- The product page shows the first **ten** non-pinned reviews, newest first.
- If more remain, a **Show more reviews** button makes a public GET (`reviews:more`) that returns the next ten, plus a replacement button if more still remain. The button replaces itself, so the list grows in place.
- Pinned reviews (the viewer's own) are excluded from every batch, so no review appears twice.
- The batching works so that Phase 6's highlighted review can join the excluded set.

### Acceptance criteria

- [ ] RED tests were written first and failed for the expected reason before implementation.
- [ ] The first batch has exactly ten reviews, newest first.
- [ ] Show more returns the next batch, and the button disappears on the last page.
- [ ] The viewer's own review is pinned and excluded from every batch. There are no duplicates across batches.
- [ ] The endpoint works signed out.
- [ ] Browser: with more than ten reviews, Show more loads in place with no reload or jump, and the button disappears at the end.
- [ ] Checks green, approval received, committed and pushed.

---

## Phase 6: Back-office Reviews tab, highlighting, and the delete-count warning

**User stories**: 51, 52, 53, 54, 55, 56, 57

### What to build

**Reviews tab**
- A staff-only, read-only, paginated list at `/backoffice/reviews/` (`reviews:manage_reviews`), newest first, with a designed empty state.
- The back-office tab rail gains a **Reviews** tab, active via `section`.
- Each row shows the product, the author's **username** (this page is staff-only), the rating, a comment excerpt, and the date.
- Each row links to the product's absolute URL with `?review=<pk>#review-<pk>`.

**Highlighting**
- On the product page, a `review` parameter that names a review **of this product** pins it below the viewer's own review with a subtle DaisyUI highlight, and excludes it from batches.
- If it's the viewer's own review, it shows only once.
- Missing, non-numeric, deleted, and other-product ids are ignored silently. The parameter affects display only, never permissions.

**Product delete confirmation**
- The back-office product delete confirmation states how many reviews will be deleted with the product.

### Acceptance criteria

- [ ] RED tests were written first and failed for the expected reason before implementation.
- [ ] Back-office access: anonymous visitors are redirected to sign-in, and non-staff get 403.
- [ ] The list is newest first and paginated, has an empty state, and shows the agreed columns.
- [ ] Rows link to the highlighted review on its product page.
- [ ] Highlighting:
  - [ ] The highlighted review is pinned below the own review and excluded from batches.
  - [ ] When the own and highlighted reviews are the same, it appears once.
  - [ ] Wrong-product, deleted, and non-numeric ids are ignored, and the page renders normally.
  - [ ] A highlighted review older than the first ten still appears pinned.
- [ ] The product delete confirmation shows the correct review count.
- [ ] Browser:
  - [ ] As staff, open the Reviews tab and follow a link to an old review. It's highlighted near the top, and the inline Edit and Delete controls work on it.
  - [ ] The product delete page shows the review count.
- [ ] Checks green, approval received, committed and pushed.

---

## Phase 7: Demo world and definition of done

**User stories**: 64, 65, 66, 67, 68, 69, 70

### What to build

The `seed` command wipes and rebuilds reviews along with the rest of the domain data, and stays destructive and idempotent. Per the PRD, it adds:

- **15–25 reviews** in the brand voice, **each backed by a `DELIVERED` order from its author** for that product.
- **4–5 reviewer-only background customers**. They, plus existing background customers, get deterministic, low-priced `DELIVERED` orders for one inexpensive showcase product. That product carries **12–13 reviews, at least 11 by users other than the demo customer**, so Show more appears for every viewer.
- **One review marked as edited by staff**.
- A delivered order for the **$39 SoulSear Authorization Case** for the demo customer, with no review for it. The demo customer also gets at least one seeded review elsewhere. **DreamWeaver and the Authorization Case** stay unreviewed.
- **No expensive Defense orders.**

Then finish the definition of done:

- Update CLAUDE.md to describe the `reviews` app, and update the README's demo notes and the seed's documentation to cover the review demo data.
- Do a full browser pass.

### Acceptance criteria

- [ ] RED tests were written first where they apply: any non-seed logic added here. Tests still never invoke the seed.
- [ ] The seed runs **twice in a row** cleanly and produces the agreed data. Verify through the shell or admin:
  - [ ] the review count
  - [ ] every review has a matching delivered order
  - [ ] the showcase product has 12–13 reviews
  - [ ] one review is staff-edited
  - [ ] the demo customer has an Authorization Case order and no review for it
- [ ] Dashboard revenue is only marginally changed, with no Defense spike.
- [ ] `uv run python manage.py migrate` applies cleanly to the existing database.
- [ ] Full browser pass, per the PRD's definition of done:
  - [ ] create, edit, and delete happen without a reload and keep the scroll position
  - [ ] Show more works
  - [ ] the page-scoped HTMX config makes 403/404 alerts swap in
  - [ ] an expired session redirects to sign-in
  - [ ] the demo customer can write a SoulSear review live
- [ ] CLAUDE.md and the README are updated, and `PROMPTS.md` records the development sessions.
- [ ] Full suite, ruff lint, and format are clean. Approval received, committed and pushed.
