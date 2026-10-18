# PROMPTS.md — AI Usage Log

This file is the record of AI use on this codebase. At the end of every
agent session, direct the agent to write the session log with this prompt:

> Append a session log to PROMPTS.md at the repo root, under today's date,
> newest entry at the top. Record every prompt I gave you this session, in
> order, including any corrections. End the entry with a short summary:
> the outcome, any places where I deviated from a recommended answer or
> asked follow-up questions, and anything that went sideways.

Two rules:

- Entries are added only by that prompt, never unprompted.
- New entries go at the top. Never rewrite or delete an old entry — the
  log is part of your work, and an honest log of a session that went
  sideways is worth more than a tidy one.

Each entry has this shape:

    ## YYYY-MM-DD — <one-line summary>

    ### Prompts
    1. ...

    ### Summary
    - **Outcome:** what was built and what was kept
    - **Deviations:** recommendations overridden, follow-up questions asked
    - **Sideways:** failures, wrong turns, and how they were caught

## 2026-10-18 — Product Reviews Phase 1: tracer bullet, reviews app and read-only Reviews section (TDD)

### Prompts
1. "Read @prd/product-reviews.md and @plans/product-reviews.md. Implement ONLY Phase 1 of the Product Reviews plan. Follow the plan's TDD workflow strictly: 1. Inspect the existing code and relevant patterns. 2. Write Phase 1 tests first and run them to demonstrate RED failures for the expected reasons. 3. Implement only enough code to make those tests pass (GREEN). 4. Run the full test suite, Ruff lint and format checks, and migration checks. 5. Provide instructions for manual browser verification. 6. STOP and wait for my approval before committing, pushing, or starting Phase 2. Do not implement later phases. Do not commit or push without my approval." (run right after a `/clear`)
2. "uv run python manage.py migrate / uv run python manage.py tailwind runserver"
3. "List the usernames of existing Django superusers in my ThoughtTronix database. Do not display or change passwords, create accounts, or modify any data. Do not change application code."
4. "wait dont"
5. "The manual browser checks for the empty Reviews state and a successful five-star review on Seraphine passed. The page displays 5.0 out of 5, 1 review, Casey M., and the Verified purchase badge correctly. Help me complete the remaining Phase 1 manual verification checks, including admin validation, escaping, unavailable products, and safe test-product deletion. Do not commit, push, or start Phase 2 until I approve."
6. "I approve Product Reviews Phase 1. The manual browser checks passed, including review display, validation, privacy, unavailable products, and product deletion cascading to reviews. Please rerun the full automated checks, document this Phase 1 session in PROMPTS.md, then commit the Phase 1 changes with the message 'Complete Product Reviews Phase 1' and push to origin. Verify git status afterward. Do not start Phase 2."

### Summary
- **Outcome:**
  - **Exploration** (prompt 1): the agent read the settings, root URLs, `conftest.py`, the product views and detail template, the order, product, coupon, and user models, the existing admin classes, and the test helpers that build orders. It ran the suite first to get a baseline (351 passed).
  - **RED** (prompt 1): to keep RED failures about behavior rather than import errors, the agent first scaffolded a bare `reviews` app. It had the `Review` fields and FKs only, with no constraints, validators, manager, display name, admin, or templates. Then it wrote 44 tests in `reviews/tests.py` (model, constraints, validation, cascades, display name, queryset, admin) and `reviews/test_product_page.py` (the Reviews section). It added three shared fixtures to `conftest.py`: `delivered_order`, `make_review`, and `named_customer`. The run showed **37 failed, 7 passed**. The failures were the expected ones: `DID NOT RAISE` for duplicates and ratings of 0 and 6, no length validation, missing `display_name`/`summary`/`newest_first`, `Review` missing from the admin, and no Reviews section on the page. The 7 that passed were cascades, order-line history, accepted comment lengths, and blank edit timestamps, which the scaffold's FKs and fields already satisfied.
  - **GREEN** (prompt 1):
    - `reviews/models.py`: `Review` with rating choices 1–5, comment `MinLengthValidator(10)`/`MaxLengthValidator(2000)`, a backdatable `created_at`, `auto_now` `updated_at`, nullable `edited_at`/`edited_by_staff_at`, the `unique_review_user_product` and `review_rating_1_to_5` constraints, and the `display_name` property ("Margaret W." / "Margaret" / "Verified customer"). `ReviewQuerySet` has `newest_first()` and `summary()`, a single `Avg`/`Count` aggregate returning a `ReviewSummary` whose `stars` rounds half up.
    - `reviews/admin.py`: `ReviewAdmin`, with the bookkeeping timestamps read-only.
    - The scaffold migration was deleted, since it was never applied, and regenerated as one clean `reviews/migrations/0001_initial.py`.
    - `ProductDetailView` adds `review_summary` and `reviews` through `product.reviews`, so `products/` gains no Python import of `reviews`.
    - `templates/products/detail.html` gets a Reviews section, with new partials `_summary.html` (with a designed "No reviews yet" empty state), `_review_card.html` (with the `review-<pk>` anchor and the Verified purchase badge, `linebreaksbr` on an autoescaped comment), and `_stars.html` (read-only DaisyUI stars).
  - **Checks:** 395 passed (351 plus 44), ruff check and format clean, `makemigrations --check` reported no changes, and `manage.py check` was clean. They were rerun before the commit with the same results.
  - **Dev server** (prompt 2): `migrate` applied `reviews.0001_initial`, and also `accounts.0002_email_ci_unique`, which the dev database had been missing since the Account Security Center. The server ran in the background.
  - **Superuser lookup** (prompt 3): a read-only shell query found one superuser, `admin`. No passwords were shown and no data was changed.
  - **Manual verification** (prompts 5–6): the user confirmed the empty state and a 5★ review by Casey M. on Seraphine. The agent looked up the real users and reviews (read-only) and wrote a step-by-step checklist: admin validation (9 characters, duplicate, rating dropdown), `<script>`/`<b>` escaping and line breaks, newest-first order, privacy searches, a signup-created `phase1tester` for "Verified customer" plus the user-delete cascade, a review on the unavailable SoulSear Mark I viewed signed out, and a throwaway "Phase 1 Test Gadget" product deleted to check the review cascade. The user reported that all checks passed and approved Phase 1.
  - **Commit** (prompt 6): `Complete Product Reviews Phase 1`, pushed to `origin`. It includes the previously untracked `prd/product-reviews.md` and `plans/product-reviews.md`, plus the PROMPTS.md entries for the grilling, PRD, and plan sessions, because those entries refer to the two files.
- **Deviations:**
  - The plan forbids RED failures caused by import errors, so the agent added a scaffold step before the tests that the user's prompt didn't mention. That left 7 tests passing at RED, and the agent reported them instead of contriving them to fail.
  - Prompt 2 was two bare commands with no instruction. The agent took it as a request to run them, and ran `migrate` and then the server in the background.
  - Prompt 4 ("wait dont") arrived after the superuser query had already finished. The agent stopped, confirmed that nothing else was running and that the query was read-only, and asked what to hold off on. The user moved on to the browser checks in prompt 5.
  - The plan says the agent runs the browser checklist and reports what it observed. The user asked for instructions instead and did the checks in the browser themselves.
  - `db.sqlite3` is gitignored but tracked since the "database and media snapshot for grading" commit. Its working copy had changed because of the migrations and the user's manual test reviews. The agent left it out of the Phase 1 commit rather than overwrite the grading snapshot, and flagged it for the user.
- **Sideways:**
  - The first browser instructions used `/products/seraphine-home-hub/`, a slug from the test fixtures and not from the seed, and the agent's smoke test got 404s. It listed the seeded slugs (`seraphine`, `soulsear-mark-i`, and so on) and corrected the checklist.
  - The Tailwind watch process quit immediately when run in the background ("Stopped watching for changes"), so the new `rating`/`mask-star-2` classes weren't compiled. Plain `tailwind build` reported "up to date" and still left the classes out; `tailwind build --force` produced them. The agent told the user that the watcher only works in their own terminal.
  - Ruff format reformatted one line in `reviews/models.py` after GREEN. The tests were rerun afterward and stayed green.

## 2026-10-18 — Product Reviews: /prd-to-plan, nine-phase proposal merged to seven, plans/product-reviews.md written

### Prompts
1. "/prd-to-plan @prd/product-reviews.md" (run right after a `/clear`)
2. "Keep the overall tracer-bullet approach, but merge proposed Phases 2 and 3 so eligibility, the form, and HTMX review creation work end-to-end in one phase. Move the proposed Phase 7 HTMX error-handling infrastructure into that merged phase, so later edit and delete endpoints reuse it. Keep the remaining phases separate, resulting in approximately 7–8 phases. Every phase must follow TDD (RED tests before GREEN implementation), automated checks, manual browser verification, my approval before proceeding, and a commit/push after approval. Do not implement anything yet. Write the plan to plans/product-reviews.md."
3. "Add an entry to PROMPTS.md documenting this /prd-to-plan session. Include the original seven-to-nine-phase proposal, my request to merge eligibility and creation and move HTMX error handling earlier, the final seven-phase plan, and any deviations or issues. Follow the existing PROMPTS.md format. Do not implement code or commit yet."

### Summary
- **Outcome:**
  - **Exploration** (prompt 1): the agent read the PRD and the saved product-reviews design notes. It looked at the project layout, the root and app URL files, `INSTALLED_APPS`, the cart's HTMX views, the template partials, the base template, the back-office tab rail, `LOGIN_URL`, the pagination sizes, and the layout of `plans/account-security.md`.
  - **Original proposal** (prompt 1): **nine** vertical slices. The header decisions were:
    - a new `reviews` app (namespace `reviews:`) that depends on `products` and `orders`
    - the `Review` model, its cascades and constraints
    - the rules kept in `ReviewQuerySet`, plus one `Order` delivered-orders queryset method
    - no service module and no signals
    - pk URLs for review actions, the back-office list under `/backoffice/reviews/`, and the product page's slug URL kept

    The nine phases were:
    1. Tracer bullet: reviews appear on the product page
    2. Who may review: eligibility and the form slot
    3. Posting a review in place
    4. Editing in place, with edit tracking
    5. Deleting in place
    6. Show more reviews
    7. HTMX failure handling: the head block, the page-scoped `htmx-config`, the alert partial, 403/404 responses with `HX-Retarget`/`HX-Reswap`, and `HX-Redirect`
    8. Back-office Reviews tab and highlighting
    9. Demo world and definition of done

    The agent flagged two choices: whether error handling should come after the create, edit, and delete phases or be built into creation, and whether Phases 2 and 3 should be merged. It then asked about granularity.
  - **The user's changes** (prompt 2):
    - Merge Phases 2 and 3 into one end-to-end create phase.
    - Move Phase 7's error handling into that merged phase, so later edit and delete endpoints reuse it.
    - Keep the other phases separate.
    - Require in every phase: TDD (RED before GREEN), automated checks, manual browser verification, the user's approval before going on, and a commit and push after approval.
  - **Final plan:** `plans/product-reviews.md`, in the `/prd-to-plan` template. The header holds the architectural decisions, an indicative URL table for the nine `reviews:` routes, and a six-step workflow shared by every phase:
    1. RED tests, shown failing for the expected reason
    2. GREEN implementation
    3. pytest, ruff check, and ruff format check, plus `makemigrations --check` when models change
    4. a browser checklist
    5. stop for approval
    6. commit (`Complete Product Reviews Phase N`), push to `origin`, and log the session in PROMPTS.md

    The seven phases are:
    1. Tracer bullet: reviews appear on the product page (stories 1–6, 9, 10, 13–15, 58, 62, 63)
    2. Writing a review in place: eligibility, form, creation, and HTMX error handling (16–35, 59, 60)
    3. Editing in place, with edit tracking (11, 12, 36–41, 46–49, 61)
    4. Deleting in place (42–45, 50)
    5. Show more reviews (7, 8)
    6. Back-office Reviews tab, highlighting, and the delete-count warning (51–57)
    7. Demo world and definition of done (64–70)

    Each phase lists its user stories, what to build, and acceptance criteria. The criteria include a RED-first check, the browser checks, and "approval received, committed and pushed."
  - The agent also updated its own saved notes on the feature (outside the repository) to record that the PRD and the seven-phase plan exist and that each phase follows the TDD and approval workflow.
  - No application code, tests, or migrations were written, and no tests were run; only read-only inspection commands were run. Nothing was committed or pushed. `plans/product-reviews.md`, `prd/product-reviews.md`, and the uncommitted PROMPTS.md entries (including this one) are pending.
- **Deviations:**
  - The user overrode the proposed order on both choices the agent had flagged. Eligibility and creation were merged, and the error handling that had come late (Phase 7) moved into the merged phase. The result is seven phases, at the low end of the "approximately 7–8" the user asked for.
  - The user added the TDD, browser verification, approval, and commit/push workflow. This is stricter than the Account Security Center plan, which had no RED-first step and no push.
  - Prompt 3 describes the original proposal as "seven-to-nine" phases. The agent actually proposed nine, and seven was the result of the merges.
- **Sideways:**
  - Nothing failed. The `/prd-to-plan` skill says to keep revising until the user approves the breakdown. Prompt 2 both set the final structure and asked for the file, so the agent treated it as approval and wrote the plan without showing the merged breakdown again.
  - The URL path strings in the plan are marked "indicative": the namespace, names, pk use, and `/backoffice/` placement are fixed, but the exact paths may change during implementation. That's a looser commitment than the Account Security Center plan's exact route table.
  - The agent didn't check whether `Order` already has a custom queryset. The plan only says the delivered-orders check is an `Order` queryset method, so Phase 2 may need to add the queryset first.

## 2026-10-18 — Product Reviews: /to-prd, five PRD clarifications, prd/product-reviews.md finalized

### Prompts
1. "/to-prd" (no arguments; run in the same conversation right after the 2026-10-17 `/grill-me` interview and its PROMPTS.md entry)
2. "I approve all five PRD clarifications: update README demo notes; seed an existing demo customer review while leaving the Authorization Case and DreamWeaver unreviewed; display only the first name when no last name exists; recheck current eligibility after deleting a review; and keep the listed extra features out of scope. Please finalize prd/product-reviews.md accordingly. Do not implement code yet."
3. "Add an entry to PROMPTS.md documenting this /to-prd session, including the prompts, the completed prd/product-reviews.md, the five clarifications, and any deviations or problems encountered. Follow the existing PROMPTS.md format. Do not change application code."

### Summary
- **Outcome:**
  - Before writing, the agent read the structure and style of `prd/account-security.md`, and checked the add-to-cart partial, the back-office tab rail, the base template's blocks, and the product delete confirmation template.
  - Prompt 1 wrote `prd/product-reviews.md` in the `/to-prd` template, without interviewing the user, matching the Account Security Center PRD's layout.
    - **Problem Statement and Solution:** written from the shopper's, customer's, and staff member's points of view.
    - **User stories:** 70, grouped into:
      - reading reviews
      - reviewer privacy
      - who can write
      - writing
      - editing
      - deleting
      - staff moderation
      - failures and edge cases
      - demo and development
    - **Implementation Decisions:** sections for:
      - owning app and architecture
      - model and database
      - eligibility and query logic
      - forms
      - views and behavior
      - HTMX error handling
      - URLs
      - templates and UI
      - admin
      - seed data
      - testing
      - definition of done
    - **Out of Scope** and **Further Notes:** the next-of-kin reasoning, why "Verified customer" is used, the add-to-cart 404 edge case under the page-scoped HTMX config, and the dashboard effect of the seed.
  - Every decision approved in the `/grill-me` entry below was carried into the PRD.
  - After the draft, the agent pointed out five places where it had filled gaps the interview hadn't settled. Prompt 2 approved all five:
    1. The README's demo notes describe the review demo data (the interview had named only CLAUDE.md).
    2. The demo customer has at least one review already seeded, while DreamWeaver and the SoulSear Authorization Case stay unreviewed.
    3. A customer with a first name but no last name shows as the first name alone ("Margaret").
    4. After an author deletes their own review, the form slot re-checks their current eligibility. They see the form if they still have a delivered order, or the not-eligible message if it was cancelled since.
    5. Extra features never discussed are kept as explicit Out of Scope boundaries: replies, helpful votes, photos, flagging, a "My reviews" page, email notifications, and review rate limiting.
  - Finalizing after prompt 2:
    - Clarifications 1, 2, 4, and 5 were already in the draft.
    - Clarification 3 was added to the display-name rule, story 13, and the display-name test.
    - A "slot after delete" test was added to the testing list.
    - The seed wording was tightened to name DreamWeaver and the Authorization Case explicitly as unreviewed.
  - No application code, tests, migrations, or plan were written, and only read-only inspection commands were run. Nothing was committed: `prd/product-reviews.md`, the 2026-10-17 entry, and this entry are all uncommitted.
- **Deviations:**
  - None from recommendations. Prompt 2 accepted all five clarifications as proposed.
  - The README update and the explicit Out of Scope items came from the agent rather than the interview. They were flagged for review instead of being added silently, and approved in prompt 2.
- **Sideways:**
  - The first draft listed a test for "customers without a last name" but never said what such a customer should display. The agent caught this when reviewing its own draft and raised it as clarification 3.
  - The first draft described the demo customer's open review slots loosely ("other delivered products (such as DreamWeaver) unreviewed"). After prompt 2, the wording was tightened to match the approved clarification exactly.
  - One edit while finalizing failed because the agent quoted the wrong anchor text ("the delete confirmation" instead of "the product delete confirmation"). It retried with the correct text, and the PRD wasn't affected.
  - The calendar date changed from 2026-10-17 to 2026-10-18 between the draft (prompt 1) and finalizing (prompt 2). This entry uses the later date.

## 2026-10-17 — Product Reviews: /grill-me design interview (23 questions plus one follow-up), design approved

### Prompts
1. "/grill-me ThoughtTronix needs a product review system. Each customer can leave one review per purchased product, including a rating and written comment. Only verified purchasers can review products, including SoulSear products; next of kin cannot. Customers can edit and delete only their own reviews. Staff can edit and delete any review. Creating, editing, and deleting reviews must update smoothly without a full-page reload or losing the customer's place. Ask me design questions one at a time, using existing project patterns when useful. Do not write code or documentation yet."
2. "Option A. Only the original purchaser can leave a review. Next of kin cannot review unless they purchased the product themselves. No additional relationship model is needed. Include a test for this rule."
3. "Option B. Only customers with a DELIVERED order containing the product can leave a review. PLACED, SHIPPED, and CANCELLED orders do not qualify. Apply this rule on the server and include tests for each order status."
4. "Option A. Verify purchase eligibility only when the review is created. Existing reviews remain if the order status changes later. Customers can still edit or delete their own reviews, and staff can edit or delete any review. Include a test confirming that a review survives cancellation."
5. "Option A. Use required whole-star ratings from 1 to 5, displayed with DaisyUI rating stars. Enforce the valid range in the model, form, and database using a CheckConstraint. No half-star or zero-star ratings."
6. "Option A. Use a required TextField with a minimum of 10 characters and maximum of 2,000. Trim leading and trailing whitespace, reject blank or whitespace-only comments, and enforce length limits in both model and form validation. Display comments safely using Django's autoescaping."
7. "Option A. Create a separate reviews app with its own models, views, URLs, templates, partials, and tests. Use the reviews URL namespace and follow the existing ThoughtTronix project conventions. Update INSTALLED_APPS and CLAUDE.md as needed during implementation."
8. "Option A. Use a custom ReviewQuerySet/manager to centralize review eligibility checks, including authentication, a DELIVERED purchase, and preventing duplicate reviews. Add a reusable Order queryset method for delivered purchases containing a product. Follow the existing CLAUDE.md conventions and keep the logic easy to test."
9. "Option A. Display and manage reviews inline on the product detail page using HTMX. Customers can create, edit, and delete their own reviews without a full-page reload or losing their scroll position. Staff can edit and delete any review. Use reusable partial templates and follow the existing cart HTMX patterns."
10. "Option A. Show clear messages based on eligibility. Signed-out visitors get a sign-in link, customers without a delivered purchase see an explanation, eligible customers see the review form, and customers who already reviewed see their own review with edit/delete controls. Staff can moderate any review but must have a qualifying purchase to create their own. Enforce all eligibility and authorization rules on the server."
11. "Option A. Use an inline HTMX confirmation swap before deleting reviews. Clicking Delete displays a DaisyUI-styled confirmation with Confirm Delete and Cancel buttons. Confirm Delete uses POST to delete the review and update the review section and summary without a full-page reload. Cancel restores the original review card. Enforce ownership and staff permissions server-side for both confirmation and deletion."
12. "Option A. Display the average star rating and total review count at the top of the product detail page's Reviews section. Calculate these using Django's Avg and Count aggregation. Use HTMX out-of-band swaps to update the summary automatically after creating, editing, or deleting reviews. Show 'No reviews yet' when there are no reviews. Keep catalog cards unchanged."
13. "Option A. Pin the signed-in customer's own review at the top, then display other reviews newest first. Show 10 other reviews initially and use an HTMX 'Show more reviews' button to load additional batches of 10 without a full-page reload or losing scroll position. Use Django's Paginator, exclude the pinned review from paginated results, and prevent duplicate reviews when loading more."
14. "Option B. Add a staff-only, read-only Reviews tab in the existing back office. Display all reviews newest first with pagination, showing the product, author, rating, comment excerpt, and date. Each review should link to its product page, where staff can edit or delete it using the existing inline HTMX controls. Use StaffRequiredMixin, follow existing back-office conventions, and avoid duplicating CRUD views. Register Review in Django admin for superuser access as well."
15. "Option A. Use ?review=<pk>#review-<pk> links from the back office to highlight and pin the selected review on its product page. Place it below the viewer's own pinned review, exclude both pinned reviews from pagination to prevent duplicates, and apply a subtle DaisyUI highlight. Ignore invalid, deleted, or wrong-product review IDs. Keep all edit/delete permissions enforced server-side, and test the edge cases."
16. "Option A. Track created_at and updated_at timestamps and display an Edited label when a review changes. Add a nullable edited_by_staff_at field to identify when staff modify another customer's review. Display 'Edited by ThoughtTronix staff' when applicable. Clear the staff-edit indicator if the original author subsequently edits the review. Keep authorization and edit tracking enforced server-side, and include tests for customer edits, staff edits, and clearing the indicator."
17. "Option A. Use on_delete=models.CASCADE for both Review.product and Review.user. Deleting a product or customer permanently deletes their associated reviews. Update the existing product delete confirmation page to show the number of reviews that will also be deleted. Preserve the existing OrderItem.product SET_NULL behavior so order history remains intact. Include tests for both cascade behaviors."
18. "Option A. Product availability should not affect review eligibility. Customers with a DELIVERED order can create reviews for unavailable or discontinued products, including the SoulSear Mark I. Existing reviews remain visible, and customers can still edit or delete their own reviews. Staff retain moderation permissions. Do not include is_available in the eligibility check. Add a test confirming that a verified purchaser can review an unavailable product."
19. "Option A. Update the seed command to create approximately 15–25 realistic reviews, each backed by a DELIVERED order from its author. Include at least one product with more than 10 reviews to demonstrate HTMX pagination and one staff-edited review. Give the demo customer a delivered order for the $39 SoulSear Authorization Case but leave their review slot open for demonstration. Avoid expensive SoulSear orders that would distort dashboard revenue. Keep the seed idempotent and ensure tests do not depend on running the seed command."
20. "Option A. Add 4–5 reviewer-only background customers and create deterministic, low-priced DELIVERED orders for a showcase product. Seed at least 12–13 reviews on that product so the HTMX Show more reviews button works in the demo, including when the demo customer is signed in. Keep paginate_by = 10, enforce one review per customer per product, preserve seed idempotency, and minimize the impact on dashboard revenue. Include tests for pagination and review eligibility."
21. "Option A. Handle HTMX review failures gracefully. Re-render invalid forms with field errors using a 200 response. For forbidden or missing reviews, preserve the correct 403/404 HTTP status codes and use HTMX response headers such as HX-Retarget and HX-Reswap to display a DaisyUI inline alert. For expired sessions, use HX-Redirect to the sign-in page with a next parameter returning to the product. Keep all authorization checks server-side, avoid extra JavaScript or dependencies, and add tests for validation errors, unauthorized requests, missing reviews, and expired sessions."
22. "Option A. Use page-scoped HTMX responseHandling configuration so 403 and 404 responses can display inline DaisyUI alerts while retaining their real HTTP status codes. Keep other pages' behavior unchanged, use HX-Retarget and HX-Reswap on review error responses, and test the status codes, alert content, and unchanged data. Verify that the configuration is recognized by HTMX 2 and that the alerts actually swap in the browser."
23. "Option A. Display each reviewer's first name and last initial, such as 'Margaret W.', falling back to their username when no first name exists. Never display email addresses or full last names on public review cards. Add a 'Verified purchase' badge to every review. Keep the display-name logic in a reusable model property or method, and test missing-name cases."
24. "Option A. Use hx-disabled-elt to disable the submit button while an HTMX request is in progress. Enforce one review per user per product with a database UniqueConstraint. Use transaction.atomic() and safely catch duplicate-review IntegrityError exceptions, returning the customer's existing review with a friendly notice instead of a 500 error. Ensure the transaction remains usable after the exception. Include tests for duplicate submissions and race conditions."
25. "Option A. Display the customer's first name and last initial when available, such as 'Margaret W.'. If the customer has no first name, display 'Verified customer' instead of their username. Never expose login usernames, email addresses, or full last names on public review cards. Keep the Verified purchase badge and add tests for both named and unnamed customers. This replaces the username fallback chosen in Question 21."
26. "I approve the design. Staff may see usernames in the staff-only back-office Reviews tab, but public reviews must never expose usernames or emails. Keep edited_at and edited_by_staff_at consistent with the agreed edit-tracking rules. The design interview is complete. Do not implement anything yet."
27. "Before moving on, add an accurate entry to PROMPTS.md documenting this completed /grill-me Product Reviews design interview. Follow the existing PROMPTS.md format and include the actual design decisions and session details. Do not modify application code yet."

### Summary
- **Outcome:**
  - The `/grill-me` interview asked 23 numbered questions plus one follow-up (Q20b), each answered by prompts 2–25. Before asking, the agent read the seed command, `orders/models.py`, the order and product views and URLs, the product detail template, the existing HTMX templates, `accounts/mixins.py`, `accounts/forms.py`, `dashboard/queries.py`, and the vendored `assets/js/htmx.min.js`. It used what it found to frame questions or answer them directly. Only read-only inspection commands were run.
  - The interview settled the design for a new `reviews` app:
    - **Who can review:**
      - Only the user on a `DELIVERED` order containing the product can review it. "Next of kin" needs no model; it's a test case for "didn't buy it."
      - Eligibility is checked only at creation, so a review survives its order later being cancelled. `is_available` is ignored, so the recalled SoulSear Mark I can be reviewed.
      - Staff moderate any review but need a qualifying purchase to write one.
    - **Model:**
      - `Review(user, product, rating, comment, created_at, updated_at, edited_at, edited_by_staff_at)`. Both foreign keys use `CASCADE`, and `UniqueConstraint(user, product)` enforces one review per product.
      - `rating`: 1–5 whole stars, enforced in the model choices, the form, and a database `CheckConstraint`.
      - `comment`: a trimmed `TextField` of 10 to 2,000 characters, validated in the model and the form, shown autoescaped.
      - `edited_at` drives the "Edited" label. `edited_by_staff_at` is set when the editor isn't the author and cleared when the author edits.
    - **Logic placement:**
      - A `ReviewQuerySet`/manager holds `eligibility(user, product)` with its reasons, the `Avg`/`Count` summary, and the listing helpers.
      - A reusable `Order` queryset method finds delivered orders containing a product.
      - No service module, so the deep modules stay at two.
    - **Product page (HTMX only):**
      - A summary block with "No reviews yet," refreshed through out-of-band swaps.
      - The form slot shows one of four states, by eligibility.
      - The viewer's own review is pinned first, then any `?review=<pk>` highlighted review, then others newest first. `paginate_by = 10` with a "Show more reviews" button, and both pinned reviews are left out of pagination.
      - Inline edit. Delete goes through an inline confirmation: Confirm Delete (POST) or Cancel.
      - A "Verified purchase" badge on every card.
    - **Errors:**
      - Invalid forms re-render with a 200.
      - 403/404 responses keep their real status and show a DaisyUI alert, aimed with `HX-Retarget`/`HX-Reswap`. A `<meta name="htmx-config">` `responseHandling` tag, scoped to the product page through a new empty `{% block head %}` in `base.html`, lets those responses swap.
      - Expired sessions get `HX-Redirect` to sign-in with `?next=`.
      - Ownership is enforced by the lookup (the cart pattern). Double submits are blocked by `hx-disabled-elt`, plus an `IntegrityError` caught in a nested `atomic()` that returns the existing review with a notice.
    - **Public identity:** "First L." or "Verified customer." No usernames, emails, or full last names on public cards. The staff-only back-office tab may show usernames.
    - **Back office:**
      - A read-only, paginated Reviews tab (`StaffRequiredMixin`, a `section` entry, an empty state) that links to `?review=<pk>#review-<pk>`.
      - The product delete confirmation shows how many reviews will also be deleted.
      - `Review` is registered in the Django admin.
    - **Seed:**
      - 15–25 reviews, each backed by a delivered order.
      - 4–5 reviewer-only customers with deterministic, low-priced delivered orders for one showcase product carrying 12–13 reviews.
      - One staff-edited review.
      - The demo `customer` gets a delivered order for the $39 SoulSear Authorization Case, with the review slot left open.
      - The seed stays idempotent, and tests never call it.
    - **Verification:** pytest cases for every rule above, plus a real browser check that HTMX 2 honors the page-scoped config and the error alerts swap in.
  - Prompt 26 approved the design.
  - No application code, tests, migrations, PRD, or plan were written, and nothing was committed. This entry is the only repository change, and it's uncommitted.
  - Outside the repository, the agent also saved a short note about the approved design to its own Claude Code memory directory, without being asked.
- **Deviations:**
  - Every numbered question took the agent's recommended option.
  - Prompt 25 (Q23) reversed prompt 23's username fallback in favor of "Verified customer." This came after the agent reported that signup collects no first name.
  - Prompt 21 (Q20) chose to keep real 403/404 status codes with `HX-Retarget`/`HX-Reswap`. The recommendation had left room for either that or a 200 response with the alert.
  - Prompt 26 confirmed two refinements the agent had added after answers. One is the `edited_at` field, replacing the `created_at`-vs-`updated_at` comparison in prompt 16. The other is usernames being allowed in the staff-only back-office tab.
  - Prompts 20, 22, and 25 answered follow-up questions the agent raised to fix problems with earlier answers (see Sideways).
- **Sideways:** four recommendations had flaws that only surfaced after the user had answered. In each case the agent caught its own mistake and raised a follow-up question; none reached code.
  - **Q15 (edit tracking):** the recommended "Edited when `updated_at` differs from `created_at`" would have labeled every new review "Edited." That's because `default=timezone.now` and `auto_now` can differ by microseconds on the first save. The agent proposed a separate nullable `edited_at` along with Q16, and prompt 26 confirmed it.
  - **Q18 (seed):** the agent recommended "at least one product with more than 10 reviews" without counting the seeded users. Only 10 exist (9 background customers plus `customer`), and with one review per user per product, the requirement couldn't be met. Background orders are also random, so reviews couldn't rely on them. The agent raised Q19, and prompt 20 added reviewer-only customers with deterministic orders.
  - **Q20 (HTMX errors):** the agent recommended using `HX-Retarget`/`HX-Reswap` to show alerts on 403/404 responses before checking how HTMX 2 behaves. After the answer, it inspected the vendored `htmx.min.js` and found that HTMX's default `responseHandling` doesn't swap 4xx responses, and those headers can't override that. As written, the alerts would never have appeared. It raised Q20b, and prompt 22 chose the page-scoped meta config. Prompt 22 also asked for browser verification that the fix works.
  - **Q21 (display name):** the agent recommended a username fallback without checking `accounts/forms.py`. Afterwards it found that `SignupForm` collects only username and email. Every customer who signs up through the site would therefore have shown their login username publicly, which undercut the privacy reasoning behind Q21. It raised Q23, and prompt 25 replaced the fallback with "Verified customer."

## 2026-10-11 — Account Security Center Phase 6: demo readiness, documentation, final PRD audit

### Prompts
1. "@prd/account-security.md @plans/account-security.md Implement Phase 6 of the approved Account Security Center plan: Final Demo, Documentation, and Verification. Read the PRD and implementation plan completely before making changes. Complete ONLY Phase 6 requirements, including: - Final demo readiness and documentation - README.md updates - .env.example updates if required - CLAUDE.md updates - Seed command documentation/docstring updates - Any remaining Phase 6 automated tests - Final verification of all six phases Perform a thorough audit against all 49 PRD user stories and their acceptance criteria. For every requirement, identify whether it is: - PASS: implemented and verified - FAIL: missing or incorrect - NEEDS MANUAL CHECK: cannot be verified automatically Do not claim requirements pass without evidence. Run: uv run pytest uv run ruff check . uv run ruff format --check . Report: 1. Files changed 2. Test results 3. PRD audit findings 4. Any missing requirements or problems 5. Exact final browser verification steps 6. Any remaining work needed before submission IMPORTANT: - Do NOT modify, restore, reset, stage, or commit db.sqlite3. - Do NOT run the seed command. - Do NOT commit or push yet. - Do NOT update PROMPTS.md yet. - Do NOT create or write REFLECTION.md. I must write my own reflection. - Wait for my review and approval. Copy prompt"
2. "Phase 6 implementation and mobile browser verification are complete. The automated checks passed: - 351 tests - Ruff lint - Ruff formatting Tasks: 1. Update PROMPTS.md with an accurate Phase 6 entry, including the original prompt, implementation decisions, automated tests, PRD audit, browser verification, and issues encountered. 2. Review all Phase 6 changes for accuracy. 3. Stage ONLY Phase 6 files and PROMPTS.md. 4. Commit with message: Complete Account Security Center Phase 6 5. Push to origin main. 6. Report the commit hash and final git status. IMPORTANT: - Do not stage, modify, restore, reset, or commit db.sqlite3. - Do not run the seed command. - Do not use git add -A or git add . - Do not create or write REFLECTION.md. - Record only browser checks actually confirmed by the user. - Stop if tests fail or unexpected files appear."

### Summary
- **Outcome:**
  - **Starting point:** Phases 1–5 were already implemented. The baseline was 342 passing tests, with ruff lint and format clean. `.env.example` already documented `DEFAULT_FROM_EMAIL` and `SUPPORT_EMAIL` (added in Phases 3–4), so it was not changed.
  - **Documentation:**
    - **`README.md`:**
      - `noemail / noemail123` added to the demo-login table, with a note that every other account has a unique `<username>@example.com` email.
      - New "Account Security Center" section: how to reach the hub, a route table, where emails appear (the dev-server terminal), and how to try a reset.
      - New "Configuration" table for `SECRET_KEY`, `DEBUG`, `ALLOWED_HOSTS`, `DEFAULT_FROM_EMAIL`, and `SUPPORT_EMAIL`, with `SUPPORT_EMAIL` flagged as a development placeholder.
      - The repo-layout paragraph said "four apps" and left out `coupons`; it now lists five.
    - **`CLAUDE.md`:** the `accounts/` entry now describes the Security Center:
      - the case-insensitive unique email constraint, which excludes blank emails
      - `User.normalize_recovery_email()` as the one normalization path
      - the two notification methods on `User`, and `mask_email()`
      - the stock reset views, with auto-login off and the 3-day default timeout
      - the console backend and the two email settings
      - no service module and no signals
      - all seven `accounts:` routes
    - **`products/management/commands/seed.py`:** docstring only. It lists all four demo logins and explains the email setup. No code changed.
  - **Tests (9 new; 351 total):**
    - `products/tests.py::test_seed_keeps_demo_recovery_emails`: after seeding twice, every demo and background account has `<username>@example.com` and `noemail` has a blank email (story 46). It follows the existing seed tests in that file, which call the seed command.
    - `accounts/test_demo_readiness.py`:
      - a transactional test that migrates `accounts` back to `0001`, creates three blank-email accounts plus one with an email, then applies `0002_email_ci_unique` cleanly
      - render checks for the three signed-in pages, the three public reset pages, and the invalid-reset-link page
  - **Extra verification by the agent (outside the test suite):**
    - **Setup:** the committed `db.sqlite3` snapshot was extracted with `git show` into the scratchpad, and a throwaway settings module pointed at that copy. The real `db.sqlite3` was never opened for writing; its checksum was unchanged.
    - **Migration:** `migrate` applied `0002` cleanly to that real, pre-feature, seeded snapshot.
    - **Live HTTP run:** with no `.env` present, the agent drove a dev server on the copy with curl:
      - Signed-in pages redirect signed-out visitors to sign in with `next`.
      - Forgot-password for `CUSTOMER@example.com` sent a reset email from the default sender.
      - The decoded link set a new password, and a weak password was rejected. The complete page linked to sign-in, the reused link showed "This reset link doesn't work", and the password-changed notice was sent.
      - Signing in with the new password and `next` returned to the hub.
      - Re-entering the current email in capitals was rejected. A padded mixed-case address was saved as `Casey.Monroe@example.com`, and the masked notice (`C***@example.com`, `support@thoughttronix.local`) went only to the old address.
      - Password change returned to the hub with its success message.
    - **Django checks:** `manage.py check` and `makemigrations --check` were clean.
  - **PRD audit (49 stories):**
    - 48 PASS, each with named-test evidence.
    - Story 39 is PASS for branding and the working link, and NEEDS MANUAL CHECK for whether the wording reads as "friendly".
    - Story 48 is PASS, with the console-wrapping caveat under Sideways.
    - Visual styling across all pages was marked NEEDS MANUAL CHECK.
    - No story was FAIL.
  - **Automated checks:** `uv run pytest` passed 351 tests. `uv run ruff check .` reported "All checks passed!", and `uv run ruff format --check .` reported 73 files already formatted. The checks were rerun after the review edits, before committing.
  - **Manual browser verification (done by the user):** the user reported that "mobile browser verification [is] complete". They did not list individual steps, so none are recorded here.
  - **Not touched:** the agent did not run the seed command. `db.sqlite3` was not modified, restored, reset, staged, or committed. PROMPTS.md was written only after the user's approval, and REFLECTION.md was not touched.
- **Deviations:**
  - No recommendation was overridden, and the user asked for no corrections.
  - **Migrate-then-seed criterion split:** the plan's acceptance criterion "migrate from the pre-feature schema on a seeded database, then seed twice" was verified in two parts. Migrate was verified on a scratch copy of the committed snapshot. Seeding twice is covered only by tests on the test database, because the user ruled out running `seed`.
  - **Manual pass:** the plan's "end-to-end manual pass of every flow" was done by the agent over HTTP on the scratch copy, not in the user's browser. The user did their own mobile browser check.
  - **Two decisions left with the user.** Both were raised in the Phase 6 report and not acted on:
    - **`db.sqlite3`:** the committed snapshot is pre-feature (accounts at `0001`, no `noemail`). The working copy holds leftover manual-test data from earlier phases: `customer` and `noemail` have `.phase4test@example.com` emails, and a `phase2test` user exists.
    - **Console wrapping:** whether to change code so console emails print unwrapped (see Sideways). Only the README note was added.
  - **Pre-existing conflict, reported but not changed:** CLAUDE.md says tests never invoke the seed command, but the existing seed tests in `products/tests.py` do.
- **Sideways:**
  - **Console emails are quoted-printable.**
    - Any line over 78 characters makes Python's email package choose quoted-printable encoding, and a reset URL is always longer than that.
    - The console therefore prints the link split across two lines with a trailing `=`, and em dashes print as `=E2=80=94`. Copying the link as printed gives an invalid link. Real mail clients decode it correctly.
    - A short experiment confirmed the cause: an ASCII body with one long line came out quoted-printable, while a short body with an em dash came out `8bit`.
    - The README now tells graders to delete the `=` and join the lines.
  - **Two false alarms came from the agent's curl script, not the app:**
    - Sign-in seemed to ignore `next` and redirect to `/`. Git Bash on Windows was rewriting the `next=/accounts/...` argument into a Windows path, which Django rightly rejected as unsafe. With `MSYS_NO_PATHCONV=1`, the redirect went to `/accounts/security/`.
    - The email and password POSTs returned 403 ("CSRF token from POST has incorrect length"). Signed-in pages carry two CSRF tokens, one in the navbar sign-out form and one in the page form, and the script had joined both. Taking the first token fixed it.
  - **Reviewing for this entry caught three inaccuracies, all fixed before committing:**
    - CLAUDE.md said all the views act only on `request.user`. It now says the signed-in ones do, because the reset views act on the user named in the link.
    - The README said every console email is quoted-printable. It now says this applies to emails with lines over 78 characters, which currently means all three.
    - The new seed test was renamed from the awkward `test_seed_keeps_every_demo_account_s_recovery_email`.
  - Writing this entry through a shell heredoc failed on quoting, so the entry was written with the editor tool and then inserted.

## 2026-10-11 — Account Security Center Phase 5: forgot password, reset link, reset confirm and complete pages, post-reset notification

### Prompts
1. "@prd/account-security.md @plans/account-security.md Implement Phase 5 of the approved Account Security Center plan: Forgot Password and Password Reset. Read the PRD and implementation plan first. Follow Phase 5 and its acceptance criteria exactly. [Requirements: use Django's built-in password reset views and token system; provide a "Forgot password?" link on the sign-in page; allow users to request a reset using their email address; show the same generic confirmation regardless of whether an account exists; send reset links using the console email backend; configure reset links to expire after 3 days; ensure reset tokens cannot be reused after a successful password change; provide the reset confirmation, new-password, and completion pages; send the required post-reset security notification according to the PRD and plan; preserve existing login, Security Center, password change, email change, and shopping functionality.] Implement ONLY Phase 5. Do not begin Phase 6. Add automated tests covering the Phase 5 acceptance criteria. Run: uv run pytest, uv run ruff check ., uv run ruff format --check . Report: 1. Files changed 2. Automated test results 3. Implementation decisions, issues, or deviations 4. Exact browser steps for manually verifying Phase 5, including the console emails. IMPORTANT: Do NOT modify, restore, reset, stage, or commit db.sqlite3. Do NOT run the seed command. Do NOT update PROMPTS.md yet. Do NOT commit or push anything. Wait for my manual browser verification and approval."
2. "Phase 5 manual browser verification is complete and approved. [The user listed ten checks and the automated results; they are recorded under Summary.] Tasks: 1. Update PROMPTS.md with an accurate Phase 5 entry, including the original implementation prompt, automated results, manual checks, implementation decisions, deviations, and problems encountered. 2. Review the Phase 5 changes and PROMPTS.md entry for accuracy. 3. Stage ONLY Phase 5 implementation files and PROMPTS.md. 4. Commit with message: Complete Account Security Center Phase 5 5. Push to origin main. 6. Report the commit hash, files committed, and final git status. IMPORTANT: Do NOT stage, modify, restore, reset, or commit db.sqlite3. Do NOT run the seed command. Do NOT use git add -A or git add . Do NOT begin Phase 6. If tests fail or unexpected files appear, stop and report before committing."

### Summary
- **Outcome:**
  - **Implementation:**
    - **`accounts/forms.py`:** `StyledPasswordResetForm` and `StyledSetPasswordForm` subclass Django's stock `PasswordResetForm` and `SetPasswordForm` and only add the DaisyUI `input w-full` class. Matching and validation are untouched: emails match ignoring capitalization; inactive, unusable-password, and blank-email accounts never match; new passwords run through `AUTH_PASSWORD_VALIDATORS`.
    - **`accounts/views.py`:** four thin subclasses of Django's reset views, each with an accounts template and an `accounts:`-namespaced success URL:
      - `ForgotPasswordView(PasswordResetView)` uses the plain-text email and subject templates in `templates/accounts/email/` and redirects to `accounts:password_reset_done`.
      - `ForgotPasswordSentView(PasswordResetDoneView)` shows the generic confirmation.
      - `ResetPasswordView(PasswordResetConfirmView)` redirects to `accounts:password_reset_complete`. Its `form_valid` calls the existing `User.send_password_changed_notification()` after Django saves the new password. `post_reset_login` stays at Django's default (off).
      - `ResetPasswordCompleteView(PasswordResetCompleteView)`.
    - **`accounts/urls.py`:** the four PRD routes, `password-reset/`, `password-reset/sent/`, `reset/complete/`, and `reset/<uidb64>/<token>/`. `reset/complete/` is listed before the confirm route.
    - **Templates (new):** `password_reset.html`, `password_reset_done.html` ("If an account matches the address you entered…"), `password_reset_confirm.html` (the new-password form when the link is valid; otherwise "This reset link doesn't work" with a "Request a new link" button), and `password_reset_complete.html` (a Sign in button linking to `accounts:login`). All extend `base.html` and match the sign-in page's card styling.
    - **Emails (new):** `email/password_reset_subject.txt` ("Reset your ThoughtTronix Store password") and `email/password_reset.txt`, a plain-text, ThoughtTronix-branded message whose link is built with `{% url 'accounts:password_reset_confirm' uidb64=uid token=token %}`. It says the link works once and expires in 3 days. The post-reset notification reuses the Phase 3 `password_changed.txt` unchanged.
    - **`templates/accounts/login.html`:** a "Forgot your password?" link to `accounts:password_reset` below the Sign in button.
    - **No settings change:** `PASSWORD_RESET_TIMEOUT` is not overridden anywhere, so Django's 3-day default holds; single use comes from Django's token, which is invalidated when the password hash changes.
    - **Tests (`accounts/test_password_reset.py`, 17 tests):**
      - the four route paths, and the sign-in page linking to `accounts:password_reset` with the text "Forgot your password?"
      - the forgot-password page is public
      - `PASSWORD_RESET_TIMEOUT` equals Django's global default of 3 days
      - a known email, a case-variant of it, an unknown email (with blank-email accounts present), an inactive account, and an unusable-password account each redirect to `accounts:password_reset_done` and get identical confirmation pages (compared with the per-session CSRF token blanked); only the first two send an email
      - the reset email goes to the stored address from `DEFAULT_FROM_EMAIL`, is branded in subject and body, is plain text only, and contains a URL that resolves to `accounts:password_reset_confirm`
      - following the link sets a new password and redirects to the complete page
      - three weak passwords are rejected, leaving the password unchanged and sending nothing
      - the complete page renders with a link to `accounts:login`, the client is not authenticated, and the user can then sign in with the new password
      - completion sends exactly one password-changed notification with "UTC" and "Forgot your password?", and with no new password, no `http`, and no token-shaped string
      - reusing the link from a fresh client shows the invalid-link page (`validlink` False), and posting to it doesn't change the password
  - **Automated checks:** `uv run pytest` passed 342 tests. `uv run ruff check .` reported "All checks passed!", and `uv run ruff format --check .` reported 72 files already formatted. The checks were rerun before committing.
  - **Manual browser verification (done by the user):**
    1. The "Forgot your password?" link opens the reset request page.
    2. A reset request for `customer.phase4test@example.com` produces the generic confirmation and a console reset email.
    3. The reset link opens the "Choose a new password" form.
    4. Weak passwords are rejected.
    5. A strong password reset succeeds and shows the completion page.
    6. The password-changed notification is sent with a UTC timestamp and recovery instructions.
    7. The customer can sign in with the new password.
    8. The original reset link cannot be reused.
    9. Unknown email requests show the same generic confirmation.
    10. The Security Center, Change Password, Update Email, product catalog, and cart still work.
  - Phase 6 was not started, and the seed command was not run. `db.sqlite3` was already modified before this session. The agent did not modify, restore, reset, stage, or commit it; the user's manual verification changed data in it.
- **Deviations:**
  - No recommendation was overridden, and the user asked for no corrections.
  - The user's prompt said "Forgot password?"; the link reads "Forgot your password?", the PRD's wording, which the password-changed notification already tells users to select.
  - The prompt said to "configure reset links to expire after 3 days". Following the plan ("No code overrides `PASSWORD_RESET_TIMEOUT`"), nothing was configured; a test pins the default instead.
  - **Implementation decisions beyond the plan's wording:**
    - The notification is sent from `ResetPasswordView.form_valid`, after `super()` saves the password, rather than through a signal, consistent with the no-signals rule.
    - The sites framework isn't installed, so the reset link's domain comes from the request (`http://127.0.0.1:8000/...` in dev).
    - The reset email uses the username, not Django's `site_name`, for branding.
- **Sideways:**
  - The first test run failed the five identical-confirmation cases: `base.html` embeds a per-session CSRF token in its HTMX `hx-headers`, so two clients never get byte-identical pages. The test now blanks that token before comparing.
  - The first attempt to patch that test through a Python heredoc mangled the regex (a backslash escape became a control character and the new constant was never inserted), which `ruff check` caught as an undefined name. The edit was redone with the editor tool, and the suite then passed.
  - `uv run ruff format` reformatted the new test module once before the checks passed.
  - The agent's Phase 5 report said 23 of the 342 tests were new; the correct number is 17 (325 after Phase 4). This was caught while reviewing for this entry.

## 2026-10-11 — Account Security Center Phase 4: update email, masked email-changed notice, SUPPORT_EMAIL

### Prompts
1. "@prd/account-security.md @plans/account-security.md Implement Phase 4 of the approved Account Security Center plan: Email Change. Read the PRD and implementation plan first. Follow Phase 4 and its acceptance criteria exactly. [Requirements: let authenticated users change their email at `/accounts/security/email/`; require the current password; validate the new email and enforce the Phase 2 case-insensitive uniqueness rule; update the email immediately after successful validation; send a security notification to the OLD address through the console email backend, including the username, a UTC timestamp, and support contact instructions; handle accounts with no existing email as the PRD and plan say; add an Email Change link to the Security Center; preserve existing account, password-change, and shopping functionality.] Implement ONLY Phase 4. Do not begin Phase 5. Add automated tests covering the Phase 4 acceptance criteria. Run: uv run pytest, uv run ruff check ., uv run ruff format --check . Report: 1. Files changed 2. Test results 3. Any issues or decisions 4. Exact browser steps for manually verifying Phase 4, including the console notification. Do not modify, restore, reset, stage, or commit db.sqlite3. Do not commit or push anything yet. Do not update PROMPTS.md yet. Wait for my manual review and approval."
2. "Phase 4 manual browser verification is complete. [The user listed ten checks; they are recorded under Summary.] Update PROMPTS.md with an accurate Phase 4 entry. Include: the original Phase 4 implementation prompt; automated results: 325 tests passed, Ruff checks passed; manual browser verification; implementation decisions, issues, and deviations. Do NOT commit or push yet. Do NOT modify, restore, reset, or stage db.sqlite3. Do NOT begin Phase 5. Show me the Phase 4 PROMPTS.md entry and git status when finished."

### Summary
- **Outcome:**
  - **Implementation:**
    - **`config/settings.py`:** `SUPPORT_EMAIL` is read through environs with the default `support@thoughttronix.local`, and a comment marks it as a development placeholder. **`.env.example`** gained a commented-out `SUPPORT_EMAIL` line with the same note.
    - **`accounts/models.py`:**
      - A module-level `mask_email()` helper returns the first character of the part before the @, then `***`, then `@` and the full domain (`sam@example.com` → `s***@example.com`, `a@example.com` → `a***@example.com`).
      - `User.send_email_changed_notice(old_email)` is called after `email` holds the new address. It renders `templates/accounts/email/email_changed.txt` with the user, `timezone.now()` in UTC, the masked new address, and `SUPPORT_EMAIL`, and sends it with `send_mail` from `DEFAULT_FROM_EMAIL` to the old address only. It returns without sending when the old address is blank.
    - **`templates/accounts/email/email_changed.txt`:** plain text, wrapped in `{% autoescape off %}` like the Phase 3 template. It has the username, the date and time labelled "UTC", the masked new address, and an instruction to contact ThoughtTronix support immediately at the support address if the change wasn't theirs. It never shows the full new address and never mentions a password reset or "Forgot your password".
    - **`accounts/forms.py`:** `EmailChangeForm` is a plain `forms.Form` that takes the user, with `current_password` and `email` fields in the DaisyUI `input w-full` style.
      - `clean_current_password` rejects a wrong password.
      - `clean_email` normalizes with `User.normalize_recovery_email`, rejects the user's own current address in any capitalization with "That's already your email address.", and rejects an address belonging to another account in any capitalization with "That email address already belongs to another account."
      - `save()` writes only the `email` field.
    - **`accounts/views.py`:** `EmailChangeView(LoginRequiredMixin, FormView)` passes `request.user` to the form. On success it records the old address, saves the form, calls `send_email_changed_notice(old_email)`, adds "Your email address has been updated.", and redirects to `accounts:security`.
    - **`accounts/urls.py`:** `security/email/` is named `accounts:email_change`.
    - **`templates/accounts/email_change.html`:** a new page styled like the password-change page. It reads "Update email" (showing the current address) or "Add email" for an email-less user, and links back to the Security Center.
    - **`templates/accounts/security.html`:** a new "Email" card with an "Update email" / "Add email" button, and the add-email reminder now has an "Add email" link to the same page.
    - **Tests (`accounts/test_email_change.py`, 22 tests):**
      - the URL path, and the signed-out redirect with `next`
      - the hub links to the page, and the reminder links there for an email-less user
      - a wrong password; another account's address in three capitalization and spacing variants; the user's own address in three variants, with the exact "That's already your email address." message; and an invalid address: each leaves the stored email unchanged and `mail.outbox` empty
      - a valid change stores the normalized address (`  Sam@Example.COM  ` → `Sam@example.com`) and redirects to the hub with the message
      - exactly one notice, addressed only to the old address, from `DEFAULT_FROM_EMAIL`, containing the username, "UTC", the masked address, and an overridden `SUPPORT_EMAIL` value, and not containing the full new address, "reset" in any case, "Forgot your password", or the password
      - adding a first email saves it, removes the reminder, and sends nothing
      - extra `user` / `username` POST fields can't change another account
      - staff and superuser can use the page
      - the notice method does nothing without an old address
      - `mask_email` on three addresses, including a one-character local part, never returning its input unchanged
  - **Automated checks:** `uv run pytest` passed 325 tests. `uv run ruff check .` reported "All checks passed!", and `uv run ruff format --check .` reported 71 files already formatted.
  - **Manual browser verification (done by the user):**
    1. Signed-out users are redirected to sign in.
    2. The Update email form is reachable from the Security Center.
    3. An incorrect current password is rejected.
    4. The user's existing email is rejected regardless of capitalization.
    5. An email address belonging to another account is rejected.
    6. A valid email change succeeds and the Security Center shows the new address.
    7. The console notification goes to the OLD address, with a UTC timestamp, the masked new email, and the support contact.
    8. An account without an email can add one.
    9. Adding a first email sends no notification.
    10. The shopping cart still works.
  - Phase 5 was not started. Nothing was committed or pushed. `db.sqlite3` was already modified before this session. The agent did not modify, restore, reset, or stage it, and the user's manual verification changed emails in it.
- **Deviations:**
  - No recommendation was overridden, and the user asked for no corrections.
  - **Implementation decisions beyond the plan's wording:**
    - The form is a plain `forms.Form` rather than a `ModelForm` on `User`. A `ModelForm` assigns the new email to the instance during validation, which would have changed `request.user` in memory even on a rejected submission.
    - The old address is recorded in the view, before `form.save()`, and handed to the notice method, which reads the new address from `self.email`.
    - `mask_email` is a module-level function in `accounts/models.py` rather than a method on `User`.
    - The page and hub button read "Add email" instead of "Update email" when the user has no address. One success message, "Your email address has been updated.", covers both cases.
    - The notice adds a line saying the old address will no longer receive messages about the account. Its wording avoids "reset" and "Forgot your password", as the plan requires.
    - The subject ("Your ThoughtTronix Store email address was changed") is a string in the model method, as in Phase 3.
- **Sideways:**
  - The first draft of the test module included a test that `SUPPORT_EMAIL` is merely set. It was removed before the first test run as low-value; the outbox test checks the setting's value through an override.
  - `uv run ruff format .` reformatted the new test module once before the checks passed. No other file needed changes.
  - When the agent rendered a sample notice in its Windows terminal, the em dash in the sign-off printed as a garbled character, as in Phase 3. This came from console encoding, not the template, and was reported to the user.
  - Reported, not fixed: if two accounts claim the same address at the same instant, the database constraint stops the second with an error page instead of a friendly form error.
  - While writing this entry, the agent's first attempt to insert it through a shell heredoc failed with a bash parse error before any file was changed. The entry was then written with the editor tool instead.

## 2026-10-11 — Account Security Center Phase 3: change password, password-changed notification, DEFAULT_FROM_EMAIL

### Prompts
1. "@prd/account-security.md @plans/account-security.md Do Phase 3. Follow the approved Phase 3 plan and its acceptance criteria exactly. Implement the password-change feature using Django's built-in password management framework. [Requirements: the page at `/accounts/security/password/`; require authentication and verify the current password; use Django's built-in password validation and hashing; keep the current session signed in; invalidate other sessions as the plan specifies; send a password-changed notification through the console email backend; put the notification in a method on the User model; include the username, a UTC timestamp, and instructions to use the sign-in page's Forgot password option if the change was unauthorized; configure `DEFAULT_FROM_EMAIL` and the email template; preserve existing account and shopping functionality.] Implement ONLY Phase 3. Do not begin Phase 4. Add automated tests for the Phase 3 acceptance criteria. Run: uv run pytest, uv run ruff check ., uv run ruff format --check . Report the files changed, test results, and any issues encountered. Explain how I can manually verify Phase 3 in the browser, including the console email notification. Do not modify or commit db.sqlite3. Do not commit or push any files yet. Wait for my manual review and approval."
2. "Phase 3 manual browser verification is complete and all checks passed. [The user listed seven checks; they are recorded under Summary.] Update PROMPTS.md with an accurate Phase 3 entry documenting: the Phase 3 implementation prompt; automated results: 303 tests passed, Ruff checks passed; all manual browser verification results; any issues, fixes, or implementation decisions. Do not commit or push yet. Do not modify, restore, reset, or stage db.sqlite3. When finished, show me the Phase 3 PROMPTS.md entry and git status."

### Summary
- **Outcome:**
  - **Implementation:**
    - **`config/settings.py`:** `DEFAULT_FROM_EMAIL` is read through environs with the default `ThoughtTronix Store <no-reply@thoughttronix.local>`. `EMAIL_BACKEND` stays the console backend, and `TIME_ZONE` stays UTC. **`.env.example`** gained a commented-out `DEFAULT_FROM_EMAIL` line.
    - **`accounts/models.py`:** `User.send_password_changed_notification()` renders `templates/accounts/email/password_changed.txt` with the user and `timezone.now()` in UTC, and sends it with `send_mail` from `settings.DEFAULT_FROM_EMAIL` to the user's email. It returns without sending when the email is blank.
    - **`templates/accounts/email/password_changed.txt`:** plain text with the username, the date and time labelled "UTC", and plain-worded advice to go to the sign-in page and select "Forgot your password?" if the change wasn't theirs. It has no link, password, or token. It is wrapped in `{% autoescape off %}` so plain-text output isn't HTML-escaped (for example, a username containing `&`).
    - **`accounts/forms.py`:** `StyledPasswordChangeForm` subclasses Django's stock `PasswordChangeForm` only to add the DaisyUI `input w-full` class, following the existing `SignInForm` pattern. Validation is unchanged: the current password must be correct, and the new one must pass `AUTH_PASSWORD_VALIDATORS`.
    - **`accounts/views.py`:** `SecurityPasswordChangeView(LoginRequiredMixin, PasswordChangeView)`. Django's `form_valid` saves the new password and calls `update_session_auth_hash`, which keeps the current session signed in. Other sessions stop authenticating because their stored session auth hash no longer matches. The view then calls the notification method, adds "Your password has been changed.", and redirects to `accounts:security`. There is no separate "done" page.
    - **`accounts/urls.py`:** `security/password/` is named `accounts:password_change`.
    - **`templates/accounts/password_change.html`:** a new page styled like the signup page, with field help text, errors, and a link back to the Security Center. **`templates/accounts/security.html`** gained a "Password" card with a "Change password" link.
    - **Tests (`accounts/test_password_change.py`, 18 tests):**
      - the URL path, and the signed-out redirect with `next`
      - the hub's link to the page
      - a wrong current password, and four failing new passwords (too short, too common, entirely numeric, mismatched): each re-renders with errors, leaves the password unchanged, and sends no mail
      - a valid change redirects to the hub with the message, and the client stays authenticated
      - a second `Client` signed in before the change is redirected to sign in afterward
      - exactly one notification from `DEFAULT_FROM_EMAIL` to the user's address, containing the username, "UTC", and "Forgot your password?", and not containing either password, `http`, or a reset-token-shaped string
      - a user with no email changes their password, sees the message, and `mail.outbox` stays empty
      - staff and superuser can use the page
      - direct unit tests of the method: it does nothing without an email, and it uses the `DEFAULT_FROM_EMAIL` setting
  - **Automated checks:** `uv run pytest` passed 303 tests. `uv run ruff check .` reported "All checks passed!", and `uv run ruff format --check .` reported 70 files already formatted.
  - **Manual browser verification (done by the user):**
    1. An incorrect current password is rejected.
    2. A common new password is rejected.
    3. A successful password change keeps the current session signed in.
    4. The console notification includes the username, a UTC timestamp, and the recovery instructions.
    5. The old password no longer works, and the new password does.
    6. Changing the password invalidates another signed-in browser session.
    7. The `noemail` account can change its password without any email being sent.
  - Phase 4 was not started. Nothing was committed or pushed. `db.sqlite3` was already modified before this session. The agent did not modify, restore, reset, or stage it, and the user's manual verification changed passwords in it.
- **Deviations:**
  - No recommendation was overridden, and the user asked for no corrections.
  - **Implementation decisions beyond the plan's wording:**
    - `LoginRequiredMixin` was added even though `PasswordChangeView` already applies `login_required`. It matches the plan's access-control decision and the hub view, and it doesn't change behavior.
    - The form subclass exists only for styling. The plan says "Django's stock form", and its validation is untouched.
    - The email subject ("Your ThoughtTronix Store password was changed") is a string in the model method rather than a separate template.
  - The plan's optional manual check for staff and superuser was covered by automated tests. The user's report didn't include a browser check of it.
- **Sideways:**
  - The first draft of the test module also included a test that `DEFAULT_FROM_EMAIL` equals its default, which skipped itself if the environment overrode the setting, and a trivial test that the method exists. Both were removed before the first test run as awkward and low-value. The `DEFAULT_FROM_EMAIL` behavior is still covered by the outbox and settings-override tests.
  - When the agent rendered a sample notification in its Windows terminal to check the wording, the em dash in the sign-off printed as a garbled character. This came from console encoding, not the template. It was reported to the user, and nothing was changed.
  - The notification tells users to select "Forgot your password?" on the sign-in page, as the plan requires. That link doesn't exist until Phase 5. This was reported to the user.
  - The agent didn't update PROMPTS.md during prompt 1, because the header says entries are added only on request. It offered to, and the user asked for this entry in prompt 2.
  - While writing this entry, the agent's first attempt to insert it through a shell heredoc failed with a bash parse error before any file was changed. The entry was then written with the editor tool instead.

## 2026-10-11 — Account Security Center Phase 2: case-insensitive unique email constraint, normalization helper, required signup email

### Prompts
1. "@prd/account-security.md @plans/account-security.md Do Phase 2. Follow the approved Phase 2 plan and its acceptance criteria exactly. [Safety requirements: before applying any migration, check both the current development database and the committed `db.sqlite3` snapshot for case-insensitive duplicate nonblank emails; if any exist, stop and report them; don't silently modify or delete accounts; don't reset, reseed, restore, or overwrite `db.sqlite3`; preserve blank-email accounts; implement the shared normalization and uniqueness rules; require and validate email at signup; use the planned constraint and migration.] Implement ONLY Phase 2. Do not start Phase 3. Run: uv run pytest, uv run ruff check ., uv run ruff format --check . Report the changes, test results, migration status, and any issues. When finished, explain how I can manually verify Phase 2 in the browser. Do not commit or push. Wait for my review and approval."
2. "Phase 2 is approved after manual browser verification. [The user listed six checks they did themselves, and one failed sign-in attempt; both are recorded under Summary.] Update PROMPTS.md with an accurate Phase 2 session log, following the existing format. Include the implementation, database safety checks, 287 passing tests, Ruff results, manual verification, and actual issues encountered. Do not invent any corrections or prompts. Do not modify application code. Do not commit or push yet. Show me the new PROMPTS.md entry and git status."

### Summary
- **Outcome:**
  - **Database safety checks:** before any migration was written or applied, both databases were checked read-only for nonblank emails that collide when capitalization is ignored, and also when surrounding whitespace is trimmed. The committed snapshot was checked through a scratch copy extracted with `git show HEAD:db.sqlite3`.
    - **Dev DB** (working-copy `db.sqlite3`): 13 users, 1 blank email (`noemail`), no duplicates.
    - **Committed snapshot:** 12 users, 0 blank emails, no duplicates.
    - The dev DB was checked again immediately before migrating and once more afterward, with the same result. No account was edited, blanked, or deleted, and `db.sqlite3` was never reseeded, reset, restored, or overwritten.
  - **Implementation:**
    - **`accounts/models.py`:** a `UniqueConstraint` on `Lower("email")` named `accounts_user_email_ci_unique`, with the condition `~Q(email="")` so blank emails are excluded. `User.Meta` inherits `AbstractUser.Meta`. A `User.normalize_recovery_email()` classmethod trims whitespace and then applies Django's `normalize_email`. `email` stays optional at the model level.
    - **`accounts/migrations/0002_email_ci_unique.py`:** one migration with a single `AddConstraint`. `makemigrations --check` reported no further changes.
    - **`accounts/forms.py`:** `SignupForm` gains a required `email` field. It normalizes the address, rejects one already in use regardless of capitalization with "That email address already belongs to another account.", and keeps the `input w-full` styling. The docstring no longer says signup asks for no email. The signup template already loops over every field, so it was unchanged.
    - **Tests:** in `accounts/test_signup.py`, the existing happy-path and password-mismatch tests now post an email. New tests cover the required field, blank and whitespace-only emails, `  Sam@Example.COM  ` stored as `Sam@example.com`, and a case-variant duplicate producing exactly one friendly field error with no non-field error. A new `accounts/test_email.py` covers the normalization helper, `IntegrityError` on case-variant duplicates through both create and update with forms bypassed, and several blank-email accounts coexisting.
  - **Migration verification:**
    - **Fresh-seeded scratch DB:** migrated to `accounts 0001`, seeded, given two extra blank-email users (three in total), then migrated. `0002` applied cleanly, and `seed` succeeded twice in a row afterward. `MEDIA_ROOT` was pointed at the scratchpad for this run.
    - **Scratch copy of the committed snapshot:** `0002` applied cleanly. The committed file itself was not touched.
    - **Dev DB:** `0002` applied. `showmigrations accounts` shows both `0001` and `0002` applied.
  - **Automated checks:** `uv run pytest` passed 287 tests. `uv run ruff check .` reported "All checks passed!", and `uv run ruff format --check .` reported 69 files already formatted.
  - **Manual browser verification (done by the user):**
    1. The signup form displays an email field.
    2. Signup is blocked when the email is blank.
    3. The `phase2test` account was created successfully.
    4. Its email was saved as `Sam@example.com`.
    5. Signup with `sam@EXAMPLE.com` was rejected as a duplicate.
    6. The existing `noemail` account still displays the add-email reminder.
  - Phase 3 was not started. Nothing was committed or pushed. `db.sqlite3` remains locally modified: it already had changes before this session, and it now also has `0002` applied and the `phase2test` account.
- **Deviations:**
  - None from the plan's acceptance criteria. The user approved Phase 2 without asking for corrections.
  - The normalization helper was placed on `User` as a classmethod rather than on a custom manager (the plan allows either). A manager subclass would have added an `AlterModelManagers` operation and broken the one-migration rule.
- **Sideways:**
  - The first generated migration also contained an `AlterModelOptions(options={})`, because the new `class Meta:` didn't inherit `AbstractUser.Meta` and so dropped the model's verbose names. This was caught by reading the migration before applying it. The migration was deleted, `Meta` was changed to inherit `AbstractUser.Meta`, and the regenerated migration contains only the `AddConstraint`. The flawed version was never applied to any database.
  - A side effect was reported to the user rather than reverted: Django's model validation checks constraints, so the Django admin now shows "An account with that email address already exists." for a duplicate instead of raising an `IntegrityError`. The PRD says admin behavior is unchanged. The user did not ask for any change.
  - Minor tooling hiccups during investigation: an `ls` of a nonexistent `accounts/tests/` directory, and a one-off `python -c` that imported Django auth without configured settings. Neither affected the work.
  - During the user's manual verification, one sign-in attempt failed because the username/password capitalization differed. Signing in with the correct credentials worked, and no application fix was needed.

## 2026-10-11 — Account Security Center Phase 1: Security Center hub, navbar link, noemail seed account, split accounts tests

### Prompts
This entry was written after Phase 1 had already been committed (`62770eb`) and pushed. The prompts from the Phase 1 implementation session aren't recorded here, and none are reconstructed. The facts below come from the user's account of that session (prompt 1) and from the commit itself. Only prompt 1 was given in this session.

1. "Read @PROMPTS.md, @prd/account-security.md, and @plans/account-security.md. Update PROMPTS.md with an accurate Phase 1 implementation session log, following its existing format. [Record the actual Phase 1 work: the hub, navbar link, noemail seed account, and split accounts tests; 271 tests passed, Ruff lint and format check passed; browser checks of customer login, Security Center, navbar greeting link, noemail warning, and shopping cart; the noemail login failure on the un-reseeded dev database, fixed by creating the account in the Django shell; commit `62770eb` pushed to GitHub; `db.sqlite3` intentionally left uncommitted.] Be transparent that this entry is being added after the Phase 1 commit. Do not invent prompts, reviews, or corrections. Do not modify application code. Do not begin Phase 2. Do not commit or push. Show me the updated PROMPTS.md entry and git status."

### Summary
- **Outcome:**
  - Phase 1 of `plans/account-security.md` was implemented and committed as `62770eb` ("Complete Account Security Center Phase 1"), then pushed to GitHub:
    - **Security Center hub:** `/accounts/security/` (`accounts:security`) in `accounts/views.py` and `accounts/urls.py`, rendered by `templates/accounts/security.html`. It shows the signed-in user's username and email, or an add-email reminder when the email is blank.
    - **Navbar link:** the "Hi, {username}" greeting in `templates/base.html` now links to the hub.
    - **Seed:** `products/management/commands/seed.py` adds the `noemail` / `noemail123` customer, with no email.
    - **Tests:** `accounts/tests.py` was split into `test_login.py`, `test_navbar.py`, `test_signup.py`, and the new `test_security.py`. `conftest.py` and `products/tests.py` gained supporting changes.
  - **Automated checks:** `uv run pytest` passed 271 tests, and `uv run ruff check .` and `uv run ruff format --check .` were clean.
  - **Browser checks:** customer login, the Security Center, the navbar greeting link, the `noemail` reminder, and the shopping cart all worked.
  - This session changed only this file. No application code was modified and Phase 2 was not started. Nothing was committed or pushed: this entry is uncommitted, and `db.sqlite3` has local changes that were intentionally left out of the Phase 1 commit.
- **Deviations:**
  - The plan's Phase 1 verification says to run `seed` first. The development database wasn't reseeded; `noemail` was created by hand in the Django shell instead (see Sideways).
  - This entry wasn't written with the header's standard logging prompt, and was added after the phase's commit rather than as part of it.
- **Sideways:**
  - Signing in as `noemail` first failed, because the development database had not been reseeded since the seed change, so the account didn't exist. It was created manually in the Django shell, and signing in as `noemail` then worked and showed the reminder.
  - The Phase 1 session's own prompts weren't logged before the commit, so this entry can't list them.

## 2026-10-11 — Account Security Center: naive draft, /prd-to-plan interview, approved six-phase plan, and comparison

### Prompts
The naive 11-step draft was written, and moved out of the repository, in an earlier session whose prompts aren't recorded here. It isn't in this repository's git history. Prompts 1–6 below were given in this session.

1. "/prd-to-plan Read @prd/account-security.md and create a tracer-bullet implementation plan for the ThoughtTronix Store Account Security Center. Save the official plan to plans/account-security.md. Follow the /prd-to-plan skill instructions. Organize the work into small, independently testable vertical-slice phases. Each phase should include the relevant implementation, tests, verification steps, and a clear stopping point. Use the existing Django project architecture and follow all approved PRD requirements. Interview me about phase granularity and any remaining implementation decisions before finalizing the plan. Do not write application code, create migrations, or implement any phases yet. After creating the proposed plan, summarize the phases and ask for my approval before considering the plan final."
   - Interview answers, selected from the agent's multiple-choice questions:
     - Granularity: "Keep 6 phases (Recommended)".
     - Seed timing for the fourth demo login: "In Phase 1 (Recommended)".
     - Fourth demo login: "noemail / noemail123".
     - Test layout: "Split modules (Recommended)".
     - `SUPPORT_EMAIL` default: "support@thoughttronix.local (Recommended)".
     - Where email normalization lives: "On the User model/manager (Recommended)".
2. "I approve the six-phase tracer-bullet implementation plan in plans/account-security.md. Keep all six phases and the agreed architectural decisions. Update the plan's status from \"proposed, awaiting approval\" to \"approved\". Do not implement any phases, create migrations, or write application code yet. Confirm the plan is finalized and ready for implementation."
3. "Compare the approved tracer-bullet plan at @plans/account-security.md with the original naive draft at ../account-security-draft.md. Explain: 1. How the phase structure and implementation order differ. 2. How the official plan delivers independently testable vertical slices. 3. How testing, verification, and stopping points differ. 4. Why the approved plan is better suited to incremental development. Do not modify either plan. Do not write application code, migrations, or tests. Do not delete the naive draft yet. Give me a concise comparison and wait for my next instruction."
4. "Update @plans/account-security.md with these two improvements identified during the naive-versus-approved comparison: 1. In Phase 2, explicitly require checking the existing database for case-insensitive duplicate nonblank email addresses before applying the unique-email migration. If duplicates exist, stop and report them rather than silently changing user data. 2. In Phase 6, explicitly require updating CLAUDE.md to document the new Account Security Center architecture and relevant account routes. Keep all six phases, approved architectural decisions, acceptance criteria, and stopping points unchanged. Do not modify the PRD or naive draft. Do not implement application code, migrations, or tests. After editing, summarize exactly what changed and confirm the plan remains approved."
5. "Update @PROMPTS.md to document the actual Account Security Center planning sessions. [Read the file first and preserve its format and all previous entries. Cover the naive 11-step draft and its move outside the repository, the /prd-to-plan interview and approved decisions, the creation and approval of the six-phase plan, the comparison, and the two post-comparison improvements. Use only supported prompts, decisions, and outcomes. Don't modify code, migrations, tests, the PRD, or either plan. Show a summary and `git status`. Don't commit or push.]"

### Summary
- **Outcome:**
  - **Naive draft** (earlier session): `../account-security-draft.md`, outside the repository. It's an 11-step plan ordered by layer:
    1. settings
    2. database constraint and helpers
    3. notification methods and email templates
    4. signup
    5. hub
    6. change password
    7. update email
    8. forgot password
    9. seed and docs
    10. all tests
    11. verification

    It ends with three open questions.
  - **`/prd-to-plan` interview:** the agent read the PRD and explored the `accounts` app, settings, navbar, seed command, `conftest.py`, and the core-platform plan. It proposed six vertical slices, then asked two rounds of questions. Decisions:
    - six phases
    - the fourth demo login is `noemail` / `noemail123`, seeded in Phase 1 so the add-email reminder can be shown right away
    - `accounts` tests split into `test_*.py` modules, like `orders/`
    - `SUPPORT_EMAIL` defaults to `support@thoughttronix.local`
    - email normalization lives on the `User` model or its manager
  - **Approved plan:** `plans/account-security.md` has the architectural decisions in its header, including the PRD's seven-route URL map, and a stopping-point checklist shared by every phase: pytest green, ruff clean, manual check, commit. The six phases are:
    1. the Security Center hub, as the tracer bullet
    2. unique emails and signup email
    3. change password with notification
    4. update email with masked notice
    5. forgot password
    6. demo world and definition of done

    Each phase lists its user stories, acceptance criteria, manual checks, and a stopping point. Prompt 2 changed its status to "approved".
  - **Comparison** (prompt 3): reported only, with no files changed.
    - The draft is ordered by layer, its tests are all saved for Step 10, it has no stopping points, and nothing a user can see works until Step 5.
    - The approved plan delivers a working, tested, committed slice each phase.
    - The draft does better on detail. Two of its details were missing from the approved plan: checking for duplicate emails before migrating, and updating CLAUDE.md.
  - **Improvements** (prompt 4), added to the approved plan:
    - **Phase 2:** before migrating any existing database (dev and the committed snapshot), check it for case-insensitive duplicate nonblank emails. If any are found, stop and report them, and change no data. A matching acceptance criterion and verification step were added.
    - **Phase 6:** update CLAUDE.md with the Security Center architecture and the seven `accounts:` routes. A matching acceptance criterion was added.

    Existing phases, decisions, criteria, and stopping points were unchanged, and the status stayed "approved".
  - No application code, migrations, or tests were written, and no tests were run. The PRD and the naive draft were not modified, and the draft was not deleted. Nothing was committed. `plans/account-security.md` and this entry are uncommitted.
- **Deviations:**
  - Every interview answer took the recommended option except the demo-login credentials. No option was marked recommended for those; the user picked `noemail` / `noemail123` over `newcomer` / `newcomer123`.
  - Prompt 3 was a follow-up comparison request. Prompt 4 adopted two gaps the comparison had flagged.
- **Sideways:**
  - The approved plan, as first written, lacked the pre-migration duplicate check and the CLAUDE.md update. The comparison caught this and prompt 4 fixed it.
  - In the first version of the plan, one Phase 5 reset case was worded confusingly ("an email belonging only to blank-email accounts"). The agent reworded it before reporting.
  - Prompt 5 asked to "append", but this file's convention puts the newest entry at the top. The entry was placed at the top.

## 2026-10-11 — Account Security Center: install skills, grill-me interview, PRD, and PRD review

### Prompts
1. "Check whether these three Claude Code skills are installed in this project: 1. /grill-me 2. /to-prd 3. /prd-to-plan Check the .claude/skills/ directory and tell me which skills exist and which are missing. Do not create or modify any files yet."
2. "Create the file .claude/skills/to-prd/SKILL.md with exactly the following content: [the to-prd SKILL.md content, pasted as a single line]"
3. "Create .claude/skills/prd-to-plan/SKILL.md with the following exact content. Preserve the Markdown formatting and line breaks. Do not create a plan or implement anything yet. [the prd-to-plan SKILL.md content]"
4. "/grill-me I want to design an Account Security Center for the ThoughtTronix Store. Customers currently can sign up, sign in, and sign out, but they need more ways to manage their account security. The new feature must let customers provide an email address when signing up, change their password while signed in, and reset a forgotten password through email. Please recommend one or two additional useful account security features that would be reasonable for this project. Interview me about the requirements and design decisions before any implementation begins. Do not write code, create a PRD, or create an implementation plan yet."
5. "I choose Option A only: allow signed-in customers to update their email address after confirming their current password. Keep the three required features: email during signup, password change, and password reset through email. Options B, C, and D are out of scope. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
6. "I choose Option B. Email addresses must be unique, enforced by both the forms and the database. Email comparisons should be case-insensitive, and existing accounts with blank email addresses should remain valid. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
7. "I choose Option B. Show a reminder in the Account Security Center for existing customers without an email address, but do not block them from using the store. Update the seed data so most demo customers have unique email addresses, but leave one demo customer without an email to test the reminder. Continue to Question 4. Do not create the PRD, plan, or implement anything yet."
8. "I choose Option A. Create a Security Center hub page at /accounts/security/ with separate pages for changing passwords and updating email addresses. Make the \"Hi, username\" greeting link to the Security Center. Add a \"Forgot your password?\" link to the login page. After successfully changing a password or email address, return the customer to the Security Center with a success message. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
9. "I choose Option A. Every signed-in user, including customers, staff, and administrators, should be able to access the Security Center and manage their own password and email address. Signed-out visitors should be redirected to login and then returned to the page they requested. Users must only be able to modify their own account. Staff should not be able to manage other users' security settings through this feature. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
10. "I choose Option B. Send a password-change notification email whenever a signed-in user successfully changes their password, as long as their account has an email address. The notification should include the time of the change and instructions to reset the password if the change was unauthorized. Do not include passwords or reset tokens in the notification. If the user has no email address, skip the email but still show the success message. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
11. "I choose Option B. Allow signed-in users to update their email address immediately after entering their correct current password and a unique new email address. If the account previously had an email address, send a security notification to the old address explaining that the email was changed and what to do if the change was unauthorized. If the account had no previous email address, skip the notification. Show a success message and return the user to the Security Center. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
12. "I choose Option A. The forgot-password page should accept an email address only and always display the same confirmation message, whether or not an account exists. Use Django's built-in PasswordResetView and related password-reset views. Keep Django's default password-reset timeout of 3 days. Reset links should be single-use and become invalid after the password changes. Accounts without email addresses or inactive accounts should not receive reset links, but the page should still show the same confirmation message. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
13. "I choose Option A. After successfully resetting their password, users should see the password-reset-complete page with a link to sign in using their new password. Do not automatically sign users in after a password reset. Send a password-change notification email after a successful reset, using the same notification approach as a password change from the Security Center. The notification should not contain passwords or reset tokens. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
14. "I choose Option A. Keep sign-in username-only using the existing username and password authentication system. Email addresses should be used for password resets, account recovery, and security notifications, but not for signing in. Do not add a custom authentication backend. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
15. "I choose Option A. Trim leading and trailing whitespace, use Django's normalize_email behavior to lowercase the domain, and preserve the user's capitalization in the local part of the email address. Continue enforcing case-insensitive uniqueness through both forms and the database. If a user enters their existing email address again, regardless of capitalization, reject it with a friendly \"That's already your email address\" validation message. Do not save any changes or send a notification. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
16. "I choose Option A. Put notification email methods on the existing User model. Use plain-text email templates under templates/accounts/email/ for password-change and email-change notifications. Configure DEFAULT_FROM_EMAIL through environs using .env, with a sensible default such as \"ThoughtTronix Store <no-reply@thoughttronix.local>\". Keep Django's console email backend for development. Real SMTP integration is out of scope. Do not create a new accounts/services.py module or use Django signals for these notifications. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
17. "I choose Option B. Send a notification to the old email address showing the new email address partially masked, such as s***@example.com. Include the username, the time of the change, and instructions to contact ThoughtTronix support immediately if the change was unauthorized. Use a configurable SUPPORT_EMAIL setting loaded through environs from .env, with a clearly documented development placeholder until a real support email is configured. Do not show the full new email address or suggest password reset as the recovery method, because reset links would now go to the new address. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
18. "I approve the proposed URL map exactly as shown, including the URL paths, names, and access rules. Keep all URLs named under the accounts namespace. Use Django's built-in password-change and password-reset views where appropriate. Use templates under templates/accounts/, extend base.html, and follow the existing DaisyUI styling conventions. After a successful password change or email update, redirect to the Security Center with a success message. Do not include user IDs or slugs in the Security Center URLs. Continue the grill interview. Do not create the PRD, plan, or implement anything yet."
19. "I choose Option B. Tests should cover successful behavior and every security rule agreed upon during the interview. Use pytest and the existing project testing conventions. Include tests for signup email validation, database uniqueness, authentication and access restrictions, password changes, email updates, password resets, notification emails, and relevant UI links. I approve the definition of done: [pytest passes; ruff clean; migration works with blank-email accounts; seed has the agreed email setup; PROMPTS.md documents the sessions]. Do not add Playwright or Selenium. If the requirements interview is complete, summarize all agreed decisions and identify any remaining questions. Do not create the PRD, implementation plan, or code yet."
20. "I approve the following final decisions: 1. Keep the project's existing UTC time zone and clearly label notification times as UTC. 2. Use a ThoughtTronix Store-branded plain-text password-reset email with friendly wording and a working reset link using the accounts namespace. 3. For very short email addresses, use masking such as a***@example.com. Never reveal the complete new email address in the old-address notification. 4. Leave Django admin and createsuperuser behavior unchanged. Friendly validation in those interfaces is outside the scope of this feature. 5. Explicitly list password-reset rate limiting and anti-spam protection as out of scope. The requirements interview is now complete. Do not implement anything or create a plan yet. Confirm that all decisions are finalized and ready for /to-prd."
21. "/to-prd Create the Product Requirements Document for the ThoughtTronix Store Account Security Center using all the finalized decisions from our requirements interview. Save the document as prd/account-security.md. Follow the /to-prd skill template, including the Problem Statement, Solution, numbered User Stories, Implementation Decisions, Out of Scope, and Further Notes. Make sure every approved security requirement is included. Do not introduce features we rejected or decisions we did not approve. Do not create an implementation plan or write application code yet."
22. "Review @prd/account-security.md against every finalized decision from our /grill-me interview. Check for missing requirements, contradictions, unapproved features, and unnecessary complexity. Pay particular attention to the 49 user stories and whether they accurately reflect our agreed scope. Do not modify the PRD yet. Report any issues you find, or confirm that it is ready for implementation planning. Do not create a plan or write application code."
23. "I approve the following decisions and PRD corrections: 1. Add a fourth demo login: a customer with a known password and no email address. Keep all existing demo accounts and their email addresses unchanged. Use the new account to demonstrate the missing-email reminder. 2. Choose Option A for password-change notifications. Use plain wording telling users to visit the sign-in page and select \"Forgot your password?\" Do not add a clickable reset link, pass the request into the model method, or introduce a new site-URL setting. 3. Clarify that notification emails must not contain passwords, reset tokens, or personalized reset links. 4. Correct the password-reset requirements to reflect Django's behavior: accounts with unusable passwords do not receive reset emails. 5. Reword Story 36 to say the forgot-password page does not reveal whether an account exists. Acknowledge that signup and email-update duplicate validation can reveal whether an email is already registered. 6. Remove the unapproved requirement about the order of form validation checks. 7. Add a test verifying that changing a password invalidates other existing sessions while keeping the current session authenticated. 8. Correct the Problem Statement to distinguish customers created through the existing signup form from seeded customers who already have email addresses. Update prd/account-security.md with these corrections. Preserve all other approved requirements and the existing scope. After editing, summarize the changes and confirm the PRD is ready for planning. Do not create an implementation plan or write application code yet."
24. "Update PROMPTS.md by appending a new entry documenting this Account Security Center requirements and PRD session. [Include the grill-me interview and major decisions, the /to-prd command, the PRD review's eight issues, the corrections, and the final outcome.] Follow the existing PROMPTS.md format. Accurately summarize the prompts and decisions from this session without inventing commands, tests, or actions. Do not modify the PRD further, create an implementation plan, or write application code."

### Summary
- **Outcome:**
  - Prompt 1 found that only `grill-me` was installed. Prompts 2–3 created `.claude/skills/to-prd/SKILL.md` and `.claude/skills/prd-to-plan/SKILL.md`.
  - The `/grill-me` interview took fifteen questions plus a final round of five small decisions. It settled:
    - **Scope:** the three required features, plus updating the email address after confirming the current password. Sign-in activity, failed-login lockout, and "sign out other devices" are out of scope.
    - **Email field:** unique, ignoring capitalization, enforced by both the forms and a database constraint that excludes blank emails. Addresses are trimmed and passed through `normalize_email`.
    - **Missing-email reminder:** shown in the Security Center and never blocking the user.
    - **Layout and access:** a hub at `/accounts/security/` with separate password and email pages, reached from the navbar greeting. Every signed-in user can use it, only on their own account.
    - **Password change:** Django's `PasswordChangeView`, plus a notification email.
    - **Email update:** takes effect immediately. A notice goes to the old address with the new address masked, pointing to a configurable `SUPPORT_EMAIL`.
    - **Password reset:** Django's built-in reset views, email only, with the same reply every time and a 3-day single-use link. There's no automatic sign-in after a reset, and it sends the same password-changed notification.
    - **Unchanged:** sign-in stays username-only.
    - **Architecture:** notification methods on `User`, plain-text templates, and `DEFAULT_FROM_EMAIL` through environs. No service module, no signals, and the console backend stays.
    - **URLs:** seven routes, all under the `accounts:` namespace.
    - **Tests:** pytest coverage of every security rule.
    - **Final round:** times labeled UTC, a branded reset email, `a***@` masking, admin and `createsuperuser` left unchanged, and reset rate limiting out of scope.
  - `/to-prd` wrote `prd/account-security.md` with 49 user stories.
  - The review (prompt 22) reported eight issues, two of which needed new decisions. Prompt 23 approved fixes for all eight, including a fourth demo login (a customer with a known password and no email) and plain "visit the sign-in page and select 'Forgot your password?'" wording in the password-changed notice. Prompt 23's corrections were applied, leaving 49 user stories.
  - The PRD was confirmed ready for `/prd-to-plan`.
  - No application code, tests, or plan were written, and no commands besides read-only inspection were run. Nothing was committed: the two new skills, the PRD, and this entry are uncommitted.
- **Deviations:**
  - Q1: the user chose A only (update email) over the recommended A + B (also sign-in activity).
  - Every other interview answer took the recommended option. Prompt 20 accepted the agent's suggested answers to the five remaining questions.
  - Prompt 22 was a follow-up review request. In prompt 23 the user chose to add the other-sessions test, rather than just noting it as Django's built-in behavior.
- **Sideways:**
  - In Q3 the agent wrongly stated that every seeded customer had no email, without checking the seed command. The user's seed answer (prompt 7) was built on that premise. During the PRD review, the agent read the seed command and found that every demo and background user already has an email, and that the background customers can't sign in. It reported its own error, and prompt 23 replaced the requirement with a fourth demo login.
  - Prompt 2's skill content arrived as a single line. The agent rebuilt the frontmatter and Markdown line breaks so the skill would load, keeping the wording unchanged, and said so.
  - The first PRD draft had four other problems, all caught in the review and fixed in prompt 23:
    - It said Django's reset form skips accounts without a usable "email"; the correct word is "password".
    - The "no reset token or link" wording was ambiguous.
    - Story 36 overclaimed that the store's customers couldn't be discovered.
    - It required a validation order that the user had never approved.
  - The password-changed notice's link needed the site's full URL, which the model method had no way to get. This was also caught in the review and resolved by using plain wording with no link.

## 2026-10-04 — Implement product images from HANDOFF.md, browser-verification fixes

### Prompts
1. "@HANDOFF.md Implement this feature"
2. "Give me a browser verification plan for the product-images feature. Tell me exactly what pages and behaviors I should manually check, including uploaded images, placeholders, back-office upload/replace/remove, validation errors, catalog display, and product detail display. Do not make any changes yet."
3. "During browser verification I noticed that the Tags multi-select on the product back-office edit form is visually broken: several tag labels run together with little or no spacing. Please make a small styling fix so each tag/checkbox option is clearly separated and readable. Keep the existing behavior and do not change anything unrelated. Then run the relevant tests and ruff."
4. "During browser verification, the Image field on the product edit page is still showing Django's default \"Currently: products/filename.webp\" and \"Clear\" UI instead of the intended current-image thumbnail/preview and clearly labeled \"Remove image (show the category placeholder)\" option. Please fix the back-office image field UI to match the agreed design while keeping the existing replace and clear behavior. Do not change unrelated functionality. Then run the relevant tests and ruff."
5. "Browser verification passed for the main product-image flows. I also manually verified that a 320x240 image is rejected with the correct plain-language validation error. Run the full test suite and ruff one final time after the browser-verification UI fixes. Do not commit anything yet."
6. "For the assignment record, the invented product is FocusForge. The image was generated using ChatGPT image generation. The image prompt/description was: \"Create a polished product image for FocusForge, a futuristic neural headband designed to improve focus and reduce distractions. Show a sleek black wearable with subtle blue lighting in a premium modern workspace setting, with FocusForge branding and the tagline 'Turn distractions into direction.'\" Do not edit PROMPTS.md yet; just keep this information in the current session so it can be included when I ask you to write the session log."
7. "Append a session log to PROMPTS.md at the repo root, under today's date, newest entry at the top. Record every prompt I gave you this session, in order, including any corrections. End the entry with a short summary: the outcome, any places where I deviated from a recommended answer or asked follow-up questions, and anything that went sideways."

### Summary
- **Outcome:** Product images were built as `HANDOFF.md` designed them:
  - Pillow was added. `MEDIA_ROOT` and `MEDIA_URL` are configured, and media is served in development when `DEBUG` is on.
  - `products/images.py` holds `validate_product_image`, `normalize_product_image`, and a thin `ProductImageField`.
  - `Product` gained an `image` field (migration `0004_product_image`) and an `image_url` property. `Product.save()` normalizes only fresh uploads, old files are deleted after the transaction commits, and a `post_delete` signal removes a deleted product's file.
  - The back-office form got a file input, a thumbnail preview, and a remove option. Catalog cards use a 4:5 frame and the detail page shows the full image.
  - Fixtures were added to `conftest.py`: an autouse temporary `MEDIA_ROOT` and an in-memory `image_upload` builder. `products/test_images.py` was added.

  All 13 provided images passed a dry run, and each came out as a WebP of 56–218 KB. The agent gave a browser verification plan. The user found two UI bugs in the browser, and both were fixed. The user then confirmed the main flows and the 320×240 rejection in the browser. The final run passed 260 tests with ruff clean. For the assignment record, the user added an invented product, **FocusForge**, with an image made by ChatGPT image generation from this prompt: "Create a polished product image for FocusForge, a futuristic neural headband designed to improve focus and reduce distractions. Show a sleek black wearable with subtle blue lighting in a premium modern workspace setting, with FocusForge branding and the tagline 'Turn distractions into direction.'" `seed` and `.gitignore` were not changed. Nothing was committed, and `media/` and `product-images/` remain untracked and should not be committed.
- **Deviations:**
  - The user overrode no recommendations, and the agent asked no clarifying questions.
  - Prompt 2 was a follow-up request for a manual browser check plan before accepting the work.
  - The agent departed from the handoff's literal wording in one place. Instead of a plain `ImageField`, it used a small `ImageField` subclass. Django's stock field checks the file extension, and its form field decodes the upload before model validators run, which would have broken the agreed rules: judge format by content, and check size first. The agent explained this when reporting, and the user did not object.
- **Sideways:**
  - **Image field UI:** the back-office image field first showed Django's default "Currently: … / Clear" widget. The template checked `widget_type == "clearablefileinput"`, but Django drops a trailing "input", so the value is `clearablefile`. The original test only checked for markup the default widget also produces, so it passed anyway. The user caught the bug in the browser (prompt 4). The check was fixed, and the tests now assert the thumbnail and the "Remove image" label, and that "Currently:" and "Change:" are absent. A test for a product with no image was also added.
  - **Tags multi-select:** this was a bug from before this session (prompt 3). DaisyUI 5's `select` class lays a control out as a one-line `inline-flex` row, which ran a `<select multiple>`'s options together. It was fixed by giving multi-selects plain Tailwind list classes, with each option on its own padded row. The widget and its behavior did not change.
  - **Smaller issues:** ruff's DJ012 rule required moving `Product.save()` above `get_absolute_url`. `tailwind build` reported the stylesheet as up to date, so `--force` was needed to compile the new classes. `media/` is now untracked, created by browser uploads; `.gitignore` can't be edited, so it has to be left out of commits by hand.

## 2026-10-04 — Product images design interview, handoff skill, and HANDOFF.md

### Prompts
1. "/grill-me Add product images to the ThoughtTronix store. Employees should be able to upload a product image through the back office, and the catalog and product detail pages should display the uploaded image when one exists or the existing category placeholder when one does not. Invalid or unusable image files must be rejected with a clear, plain-language error message. We also need to make reasonable decisions about accepted image formats, maximum file size, image consistency, storage, and validation. The provided product images are in the product-images directory in the repository root."
2. "I agree with A. Use Django's media system with ImageField and MEDIA_ROOT, store uploaded product images on the local filesystem, and keep the media directory gitignored."
3. "I agree with A. Accept JPEG, PNG, and WebP only. Validate the image based on its actual format rather than just the file extension, and give the employee a clear error message such as \"Please upload a JPEG, PNG, or WebP image.\""
4. "I agree with B. Set the maximum product image upload size to 5 MB. Use a named constant for the limit and give the employee a clear error message that includes the uploaded file's size and says the maximum is 5 MB."
5. "I agree with B. Normalize uploaded images by fixing EXIF orientation, resizing them so the longest side is at most 1200 px, and saving them as WebP. The 5 MB upload limit should still be checked before processing."
6. "I agree with B. Use a fixed 4:5 frame with object-cover for product images on the catalog page so the cards stay consistent. On the product detail page, display the full image without cropping."
7. "I agree with B. Require images to be at least 600 pixels on the shortest side. Also use a maximum of 6000 pixels per side as a safety limit. Give a clear error message that shows the uploaded image dimensions when it does not meet the requirements."
8. "I agree with B. Let employees preview the current image, replace it, or clear it so the product falls back to its category placeholder. Delete the old image after a successful transaction when an image is replaced, cleared, or the product is deleted. Use the product slug plus a short random suffix for stored filenames, such as products/seraphine-3f9a1c.webp."
9. "I prefer C. Do not change the seed command to attach the provided images, and do not commit the product-images directory. The provided product-images folder should remain temporary and will be used to manually upload images through the back office for testing. Seed should continue creating the normal demo data without uploaded product images."
10. "I agree with A. Use a post_delete signal so product image files are cleaned up whether a product is deleted through the back office or through seed's bulk delete. After reseeding, uploaded product images can be manually uploaded again. Do not modify .gitignore for product-images/. I will make sure that temporary folder is not committed."
11. "I agree with A. Put the reusable image validation and normalization functions in products/images.py, use the validator on the Product ImageField, and normalize newly uploaded or replaced images through the model save path. Make sure an existing image is not reprocessed when unrelated product fields are edited. The same validation rules should apply through both the back office and Django admin."
12. "No, don't save a separate plan or implement anything yet. The design is settled."
13. "/skills", then "/anthropic-skills:skill-creator" (no arguments)
14. "Create a project skill named handoff. It should capture the important context and all decisions from the current session into HANDOFF.md so that a fresh Claude Code session can continue the work without needing the previous conversation. It should accept instructions after /handoff describing what the next session should do. Do not implement the feature itself."
15. "/handoff the next session implements the design we just agreed"
16. "Update HANDOFF.md so it does not instruct the next session to modify .gitignore at all. The assignment says not to edit .gitignore. Keep product-images/ temporary and uncommitted. Do not change anything else in the handoff."
17. "Read the header of PROMPTS.md and tell me the exact standard prompt it says to use for writing a session log. Do not edit any files yet."
18. "Remove only the instruction in HANDOFF.md that tells the next session to append its session to PROMPTS.md automatically. Do not change anything else."
19. "Append a session log to PROMPTS.md at the repo root, under today's date, newest entry at the top. Record every prompt I gave you this session, in order, including any corrections. End the entry with a short summary: the outcome, any places where I deviated from a recommended answer or asked follow-up questions, and anything that went sideways."

### Summary
- **Outcome:** The grill-me interview took ten questions and settled the whole product-images design:
  - local `ImageField` storage, with slug-plus-suffix `.webp` filenames;
  - JPEG, PNG, or WebP only, judged by the real format;
  - a 5 MB upload limit, checked first;
  - 600–6000 px dimension limits;
  - normalization to EXIF-corrected, 1200 px WebP;
  - a 4:5 cropped catalog frame and an uncropped detail image;
  - back-office preview, replace, and clear;
  - after-commit file cleanup, with a `post_delete` signal;
  - no change to `seed`;
  - validation and normalization in `products/images.py`, so the admin enforces the same rules.

  The session then created the project skill `.claude/skills/handoff/SKILL.md` and used it to write `HANDOFF.md` for the next session. No feature code was written. Nothing was committed. The handoff skill, `HANDOFF.md`, this entry, and the existing `product-images/` folder are all uncommitted.
- **Deviations:**
  - Q8 (seed): the user chose C (leave seed unchanged, don't commit the images) over the recommended A (seed attaches the provided images from a committed folder).
  - Q9: the user declined the offered `.gitignore` entry for `product-images/`.
  - The user declined the offer to save the design as `plans/product-images.md`.
  - Prompt 16 reversed part of prompt 2 ("keep the media directory gitignored"), because the assignment forbids editing `.gitignore`.
  - Prompt 17 was a follow-up question about the `PROMPTS.md` header.
- **Sideways:**
  - The first `HANDOFF.md` told the next session to add `media/` to `.gitignore`. That matched prompt 2 but broke the assignment's no-`.gitignore` rule; prompt 16 corrected it.
  - The agent also added an unrequested constraint to `HANDOFF.md`, telling the next session to append its own session to `PROMPTS.md`. That contradicts this file's rule that entries are added only by the standard prompt. The problem came to light at prompt 17 and was removed in prompt 18.
  - The first draft of `HANDOFF.md` wrongly claimed that `ClearableFileInput` doesn't subclass `forms.Input`. The agent caught and fixed this before reporting.
  - The handoff skill skipped skill-creator's eval loop, because test runs can't see the conversation that the skill reads. Its first real test was prompt 15.

## 2026-09-27 — Commit the coupon product checkbox selector, plus session log

### Prompts
1. "Run uv run python manage.py tailwind runserver"
2. "The improved Products checkbox selector looks correct in the browser. Commit and push this post-review improvement with a descriptive commit message. Do not make any additional code changes."
3. "Write this session log to PROMPTS.md using the standard prompt in the PROMPTS.md header."

### Summary
- **Outcome:** Started the dev server with Tailwind watch in the background and confirmed that the home page returned HTTP 200. After the user checked the Products checkbox selector in the browser, the three changes already in the working tree were committed as `ab28359` ("Use labeled checkboxes for coupon product selection") and pushed to `origin/main`. Those changes were in `coupons/forms.py`, `coupons/test_backoffice.py`, and `templates/products/partials/_field.html`. No code was written or edited in this session. The only file changed was this one, by prompt 3.
- **Deviations:** None. No recommendations were made or overridden, and no follow-up questions were asked. The commit went straight to `main`, which matches the earlier commits.
- **Sideways:** Nothing failed. The dev server's log file was still empty right after it started, so the agent confirmed the server was up by requesting the page instead. Before committing, the agent ran the full test suite (232 passed); this wasn't asked for, and it changed no code. The checkbox selector itself was built in an earlier session whose prompts aren't recorded here, and neither is the coupon feature from `fe75948`.

## 2026-09-20 — Featured products, plus session log

### Prompts
Prompts 1–3 were given in earlier Claude sessions today; prompts 4–5 were given in this session.

1. "Add an is_featured Boolean field to the Product model with a default value of false."
2. "Run the migration."
3. "Show a \"Featured\" badge on featured products on both the catalog listing page and the product detail page."
4. "Append a session log to PROMPTS.md at the repo root, under today's date, newest entry at the top. Record every prompt I gave you this session, in order, including any corrections. End the entry with a short summary: the outcome, any places where I deviated from a recommended answer or asked follow-up questions, and anything that went sideways."
5. "Update today's PROMPTS.md entry to include the Featured Products prompts I gave you in the earlier Claude sessions today: [prompts 1–3]. Keep the logging prompt that is already recorded. Do not change any code."

### Summary
- **Outcome:** Prompts 1–3 correspond to the commits `67d9ba9` (add featured product field) and `0437171` (add featured product badges) on `main`. Prompts 4–5 changed only this file; no code was touched in this session.
- **Deviations:** None recorded for this session. The earlier sessions' transcripts were not available when this entry was written, so whether any recommendations were overridden or follow-up questions were asked in them is not captured here.
- **Sideways:** Nothing failed in this session. Prompts 1–3 were supplied by the user from memory of the earlier sessions, not read from a transcript. Prompt 4 was first logged on its own, and prompt 5 corrected that by adding the earlier prompts.
