# PRD: The ThoughtTronix Store — Product Reviews

*Commissioned by ThoughtTronix Product Management. "Your Thoughts, Our Business."*

---

## Problem Statement

Shoppers at the ThoughtTronix Store have nothing to go on but the company's own product copy. A product page shows a name, a price, a tagline, and a description written by marketing, and that is all. Nobody who has actually lived with a Seraphine, worn a MindSync, or taken delivery of a SoulSear can tell the next shopper what it was like.

That leaves several groups stuck:

- A shopper deciding between products can't see how other customers rated them or what they said.
- A customer who received a product has nowhere to share their experience, good or bad.
- Without a rule about who may post, any feedback system could be filled by people who never bought the product: curious onlookers, competitors, or the next of kin of customers involved in certain SoulSear incidents. Reviews are only worth reading if they come from people who actually received the product.
- Staff have no way to see what customers are saying, or to correct or remove a review that shouldn't be there.

Customers also expect posting, fixing, or removing a review to feel instant. A page that reloads and throws them back to the top after every action is frustrating, especially on a long product page.

## Solution

Every product page gains a **Reviews section**. At the top is a summary: the average star rating and the number of reviews, or "No reviews yet." Below it, each review shows a 1–5 star rating, a written comment, the reviewer's first name and last initial (or "Verified customer"), the date, and a **Verified purchase** badge.

Only a **verified purchaser** can write a review: a customer whose own account has a **delivered** order containing that product. Each customer gets one review per product. Someone who didn't place a delivered order (including a buyer's next of kin) is told why they can't review. This applies to every product, including SoulSear products and products no longer for sale.

Customers can edit and delete their own reviews. Staff can edit and delete any review, and an edit by staff is labeled as such. Creating, editing, and deleting all happen **in place on the product page** using HTMX: the review card or form changes, the summary updates, and the page never reloads or loses the customer's scroll position. Deleting asks for confirmation inline first.

A customer's own review is pinned at the top of the list, and the other reviews follow newest first, ten at a time, with a **Show more reviews** button.

Staff get a read-only **Reviews** tab in the back office listing every review, newest first. Each entry links straight to that review on its product page, where it's highlighted and pinned so staff can moderate it with the same inline controls.

## User Stories

### Reading reviews

1. As a shopper, I want to see a Reviews section on every product page, so that I can learn what other customers think before I buy.
2. As a shopper, I want to see the average star rating and the total number of reviews at the top of the Reviews section, so that I can judge a product at a glance.
3. As a shopper, I want to see "No reviews yet" on a product nobody has reviewed, so that the section never looks broken or empty.
4. As a shopper, I want each review to show its star rating, written comment, reviewer name, and date, so that I can weigh each opinion.
5. As a shopper, I want every review to carry a "Verified purchase" badge, so that I know it came from someone who actually received the product.
6. As a shopper, I want reviews shown newest first, so that I see the most current opinions.
7. As a shopper, I want to see ten reviews at first and load ten more at a time with a "Show more reviews" button, without the page reloading or jumping, so that long review lists stay fast and I keep my place.
8. As a shopper, I never want to see the same review twice while loading more, so that the list is trustworthy.
9. As a shopper, I want to read reviews of products that are no longer for sale, such as the recalled SoulSear Mark I, so that I can learn from past owners.
10. As a shopper, I want to read reviews without signing in, so that I can research products freely.
11. As a shopper, I want to see "Edited" on a review that was changed after it was posted, so that I know it isn't the original wording.
12. As a shopper, I want to see "Edited by ThoughtTronix staff" on a review that staff changed, so that I never mistake a company edit for the customer's own words.

### Privacy of reviewers

13. As a customer, I want my review to show only my first name and last initial (for example "Margaret W."), or just my first name if I have no last name on file, so that my full name isn't public.
14. As a customer who signed up without giving a first name, I want my review to show "Verified customer," so that my login username is never revealed.
15. As a customer, I want my email address, username, and full last name never to appear on a public review, so that nobody can use my review to target my account.

### Who can write a review

16. As a customer with a delivered order containing a product, I want to see a review form on that product's page, so that I can share my experience.
17. As a signed-out visitor, I want to see a "Sign in to review products you've purchased" link that brings me back to the same product after signing in, so that I can review without hunting for the page again.
18. As a signed-in customer without a delivered order for a product, I want to see a short message explaining that only customers with a delivered order can review it, so that I understand why there's no form.
19. As a customer whose order is still placed or shipped, I want to be told I can't review yet, so that I only review products I've actually received.
20. As a customer whose order was cancelled, I want to be unable to review that product from that order, so that reviews come only from real deliveries.
21. As the next of kin of a customer, I am unable to review a product my relative bought unless I bought and received it myself, so that only actual purchasers speak for a product.
22. As a customer who has already reviewed a product, I want to see my own review (with Edit and Delete) instead of a new form, so that I can't accidentally post twice.
23. As a customer, I want to be able to review SoulSear products I've received, so that defense customers have the same voice as everyone else.
24. As a customer, I want to be able to review a product I received even after it stops being sold, so that a recall or discontinuation doesn't silence me.
25. As an employee, I want to be able to write my own review only if I have a delivered order for the product myself, so that "Verified purchase" stays true for staff too.
26. As a customer, I want the store to refuse any review I'm not allowed to post, even if I bypass the page, so that the rules can't be worked around.

### Writing a review

27. As a customer, I want to pick a rating of 1 to 5 whole stars, so that I can rate quickly in a familiar way.
28. As a customer, I want the store to require a rating, so that every review contributes to the average.
29. As a customer, I want to write a comment of 10 to 2,000 characters, so that my review says something meaningful without taking over the page.
30. As a customer, I want a comment made only of spaces to be rejected, and extra spaces at the start and end to be trimmed, so that blank or sloppy reviews aren't posted.
31. As a customer, I want my form to come back with clear field errors when something is wrong, without losing what I typed or reloading the page, so that I can fix it easily.
32. As a customer, I want my new review to appear pinned at the top of the list and the summary to update immediately after I post, without a page reload, so that I can see it worked.
33. As a customer, I want the submit button disabled while my review is being posted, so that a double click doesn't cause a problem.
34. As a customer who submitted the same review twice at once (for example from two tabs), I want to see my existing review with a friendly notice instead of an error page, so that nothing breaks and I still get one review.
35. As a customer, I want anything I type to be shown as plain text, so that nobody can inject code or formatting into a review.

### Editing a review

36. As a customer, I want an Edit button on my own review that turns the card into a form in place, so that I can fix my review without leaving the page.
37. As a customer, I want Save to update my review in place and Cancel to restore it unchanged, so that editing is quick and safe.
38. As a customer, I want the summary to update after I change my rating, so that the average stays correct.
39. As a customer, I want to be able to edit my review even if my order was later cancelled or the product stopped being sold, so that I can always keep my own words accurate.
40. As a customer, I want no Edit or Delete buttons on other customers' reviews, and the store to refuse any attempt to change them, so that my review can only be changed by me or staff.
41. As a customer whose review was edited by staff, I want my next edit to remove the "Edited by ThoughtTronix staff" label, so that the label disappears once the words are mine again.

### Deleting a review

42. As a customer, I want clicking Delete on my review to show an inline confirmation ("Delete this review? This can't be undone.") with Confirm Delete and Cancel, so that I don't delete it by accident.
43. As a customer, I want Confirm Delete to remove my review and update the summary without a page reload, so that the change is instant.
44. As a customer, I want Cancel to bring my review card back unchanged, so that backing out is easy.
45. As a customer who deleted my review, I want the form slot to show whatever applies to me now (a fresh form if I still have a delivered order), so that I can review again if I change my mind.

### Staff moderation

46. As an employee, I want Edit and Delete controls on every review on every product page, so that I can moderate in place.
47. As an employee, I want to change any review's rating or comment with the same inline form customers use, so that moderation needs no separate tool.
48. As an employee, I want my edits to another customer's review to be labeled "Edited by ThoughtTronix staff," so that shoppers can trust what they read.
49. As an employee, I want my edits to my own review to count as a normal author edit, so that the staff label only marks changes to someone else's words.
50. As an employee, I want to delete any review with the same inline confirmation, so that harmful or mistaken reviews can be removed.
51. As an employee, I want a Reviews tab in the back office listing every review newest first, with pagination and a designed empty state, so that I can scan what customers are saying in one place.
52. As an employee, I want each row to show the product, the author's username, the rating, a comment excerpt, and the date, so that I can identify the review and the account behind it.
53. As an employee, I want each back-office row to link to the review on its product page, so that I can moderate it with the inline controls.
54. As an employee, I want that link to highlight the review and pin it near the top of the product page, even if it's an old review beyond the first ten, so that I never have to dig for it.
55. As an employee, I want the highlight to show the review only once on the page, so that the list stays clean.
56. As an employee, I want a stale or wrong review link to simply show the product page normally, so that a bad link never causes an error.
57. As an employee, I want the product delete confirmation to tell me how many reviews will also be deleted, so that I understand the consequence before I confirm.
58. As the administrator, I want reviews available in the Django admin, so that I have superuser-level access to the data.

### Failures and edge cases

59. As a customer, I want to see an inline alert such as "This review is no longer available" when I act on a review that was deleted in another tab or that I'm not allowed to change, so that the page never silently does nothing.
60. As a customer whose session expired, I want an action on a review to take me to the sign-in page and then back to the product, so that I'm never shown a sign-in page squeezed inside a review card.
61. As a customer, I want my review to stay if my order is later cancelled, so that a later change in the order doesn't erase what I wrote.
62. As a customer, I want my reviews deleted when my account is deleted, so that nothing I wrote lingers after I leave.
63. As a shopper, I want a deleted product's reviews to go with it, so that no orphaned reviews remain.

### Demo and development

64. As a demonstrator, I want the seeded demo world to include realistic reviews on several products, so that the feature looks lived-in right after seeding.
65. As a demonstrator, I want one product to have enough reviews that "Show more reviews" appears, even when signed in as the demo customer, so that I can demonstrate loading more.
66. As a demonstrator, I want one seeded review to be marked as edited by staff, so that I can show the staff-edit label.
67. As a demonstrator, I want the demo customer to have a delivered order for the SoulSear Authorization Case with no review yet, so that I can demonstrate writing a SoulSear review live.
68. As a developer, I want every seeded review backed by a delivered order from its author, so that the seed follows the same rules as the store.
69. As a developer, I want the seed's extra orders to be cheap, so that the dashboard's revenue charts aren't distorted.
70. As a developer, I want the seed to stay destructive and idempotent, and the tests never to depend on it, so that the existing conventions hold.

## Implementation Decisions

### Owning app and architecture

- A new **reviews** app owns the feature: its model, manager, forms, views, URLs, templates, partials, and tests. Its URLs live under the **`reviews:`** namespace. It is added to the installed apps, and the project's CLAUDE.md is updated to describe it.
- Dependencies point one way: **reviews depends on products and orders**. Neither of those depends on reviews, apart from the product detail page including the Reviews section and the product delete confirmation showing a review count.
- The project's conventions apply: logic lives in models and managers, views are thin class-based views, forms own their validation.
- **No service module is added.** Eligibility is a check, not a cross-model workflow, and the project keeps exactly two deliberate deep modules (order placement and dashboard queries). No Django signals are used.

### Review model and database

- A new **`Review`** model with:
  - **`user`**: foreign key to the user model, **cascade on delete**.
  - **`product`**: foreign key to `Product`, **cascade on delete**.
  - **`rating`**: a small positive integer limited to whole-star choices **1–5**, required.
  - **`comment`**: a text field, required.
  - **`created_at`**: defaults to the current time (not auto-set), so tests and the seed can backdate reviews, matching how orders work.
  - **`updated_at`**: set automatically on every save, for bookkeeping only.
  - **`edited_at`**: nullable. Set whenever an existing review is changed. This field, not a comparison of `created_at` and `updated_at`, drives the "Edited" label, because those two can differ by microseconds on the first save.
  - **`edited_by_staff_at`**: nullable. Set when the person saving an edit is not the review's author. **Cleared** when the author later edits. A staff member editing their own review counts as an author edit.
- **Database constraints:**
  - A **unique constraint on (user, product)**: one review per customer per product.
  - A **check constraint** keeping `rating` between 1 and 5.
- **Validation layering:**
  - Rating range: model choices, form, and database check constraint.
  - Comment: the form trims leading and trailing whitespace and rejects blank or whitespace-only text. Minimum (10) and maximum (2,000) lengths are enforced by model validators and the form, so the admin respects them too.
- Existing order history behavior is unchanged: an order line's product link still becomes empty when a product is deleted.

### Eligibility and query logic

- A reusable **`Order` queryset method** returns delivered orders containing a given product. "Delivered" means the `DELIVERED` status only. `PLACED`, `SHIPPED`, and `CANCELLED` do not qualify. The orders app owns this definition.
- A custom **`ReviewQuerySet`/manager** is the single source of review rules:
  - **Eligibility for (user, product)** returns whether the user may create a review and, if not, the reason: **signed out**, **no delivered purchase**, or **already reviewed**. The views, the template's form slot, and the tests all use it.
  - Eligibility looks only at the user's own delivered orders and existing reviews. **Product availability is not considered.** Staff status grants no exemption.
  - Eligibility is checked **only at creation**. After a review exists, editing and deleting depend only on authorship (or staff status). A review survives its order later being cancelled.
  - The **summary** (average rating and count) is a single aggregate using `Avg` and `Count`, computed live with nothing stored.
  - Listing helpers return a product's reviews newest first, excluding given reviews (the pinned ones) for pagination.
- **Public display name** is a reusable model method or property: first name plus last initial ("Margaret W.") when both names exist, **the first name alone ("Margaret") when there is no last name**, otherwise **"Verified customer."** It never returns a username, email, or full last name. (Signup collects no first name, so "Verified customer" is the normal case for customers who signed up through the site.)

### Forms

- **Review form:** rating (rendered as DaisyUI rating stars, radio inputs, no JavaScript) and comment. The same form is used for create and edit, by customers and staff.
- The form validates the rating range and the comment rules. Duplicate prevention is enforced by eligibility on create and by the database constraint.
- Recording who edited (setting `edited_at`, and setting or clearing `edited_by_staff_at`) happens in the form's or model's save path, not in the view.

### Views and behavior

- All review interactions are HTMX endpoints that return partials, following the cart's pattern. Every state change is a POST.
- **Create (POST):** signed-in only. The server re-checks eligibility; an ineligible create returns **403** and saves nothing. On success it returns the new review as the pinned own-review card, plus the summary as an out-of-band swap. Invalid input re-renders the form partial with field errors and a **200**.
- **Duplicate race on create:** the save runs inside a nested atomic block. If the unique constraint raises an integrity error, it is caught (leaving the outer transaction usable) and the response shows the customer's existing review with a friendly notice and a 200, never a 500.
- **Edit form (GET), Save (POST), Cancel (GET):** Edit swaps the card into the form, Save updates the review and returns the card plus the refreshed summary, and Cancel returns the unchanged card.
- **Delete confirmation (GET), Confirm Delete (POST), Cancel (GET):** the confirmation GET changes nothing and swaps the card into a DaisyUI-styled confirmation. Confirm Delete removes the review, removes the card, refreshes the summary out of band, and, when the author deletes their own review, re-renders the form slot according to their current eligibility. Cancel restores the card.
- **Ownership is enforced by the lookup**, as in the cart: a customer's edit and delete endpoints fetch only from their own reviews, and staff fetch from all reviews. Someone else's review, or one that no longer exists, is a **404**. This applies to the edit form and the delete confirmation as well as the POSTs.
- **Show more (GET):** public. Returns the next batch of ten reviews plus a new "Show more reviews" button if more remain. The button replaces itself, so the list grows in place. The pinned reviews (the viewer's own and any highlighted one) are excluded, so nothing appears twice.
- **Product detail page:** builds the Reviews section context: the summary, the eligibility state for the form slot, the viewer's own review (pinned), an optional highlighted review, and the first page of other reviews.
- **Highlighted review:** a `review` query parameter naming a review **of this product** pins it below the viewer's own review with a subtle DaisyUI highlight, and it is excluded from pagination. If it is the viewer's own review, it shows once. Missing, non-numeric, deleted, or other-product ids are ignored silently. The parameter only affects display, never permissions.
- **Back-office review list:** a staff-only, read-only, paginated list view using the existing staff mixin, a `section` entry for its tab, and a designed empty state. It has no edit or delete screens of its own.
- **Product delete confirmation:** shows the number of reviews that will be deleted with the product.

### HTMX error handling

- **Validation errors** re-render the form partial with a 200.
- **403 and 404** responses from review endpoints keep their **real status codes**, carry a DaisyUI inline alert partial, and use **`HX-Retarget` and `HX-Reswap`** headers to aim the alert at the affected card. A refreshed summary accompanies the alert where relevant, so the page doesn't go stale.
- HTMX 2 does not swap 4xx responses by default, and those headers cannot override that. So the product detail page, **and only that page**, carries an **HTMX `responseHandling` configuration** in an `htmx-config` meta tag:
  - 204: no swap
  - 2xx and 3xx: swap
  - 403 and 404: swap, marked as errors
  - other 4xx and 5xx: no swap

  The base template gains an empty head block for this. Every other page keeps HTMX's defaults.
- **Expired sessions:** an anonymous HTMX request to a review endpoint receives an **`HX-Redirect`** header pointing to the sign-in page with a `next` parameter that returns to the product page. A non-HTMX anonymous request gets the normal sign-in redirect.
- Double clicks are prevented with **`hx-disabled-elt`** on the review form's submit button. No JavaScript is written beyond HTMX attributes and configuration, and no new dependencies are added.

### URLs

- All review URLs are named under the **`reviews:`** namespace: create (per product), edit form, update, cancel edit, delete confirmation, delete, cancel delete, show more (per product), and the back-office list.
- Customer- and staff-facing review actions use pks, since they act on a specific review or product. The public product page keeps its slug URL.
- The back-office list lives under the back-office URL area. Its links go to the product's absolute URL with the highlight parameter and an anchor for that review.

### Templates and UI

- The product detail page includes the Reviews section below the product information.
- Reviews partials follow the project's underscore-prefixed naming convention and never extend the base template. They cover:
  - the review summary
  - a review card
  - the review form
  - the form slot's states (sign-in link, not-eligible message, form, own review)
  - the delete confirmation
  - the "Show more" batch
  - the inline alert
- Each review card has a stable anchor id based on its pk, so links and swaps can find it.
- The card shows stars, the comment (autoescaped, line breaks preserved), the public display name, the posted date, a "Verified purchase" badge, an "Edited" label when `edited_at` is set, and "Edited by ThoughtTronix staff" when `edited_by_staff_at` is set. Edit and Delete appear only for the author and for staff.
- The back office's tab rail gains a **Reviews** tab.
- Styling is Tailwind and DaisyUI classes only, in the `night` theme.

### Admin

- `Review` is registered in the Django admin for superuser access.

### Seed data

- The seed wipes and rebuilds reviews along with the rest of the domain data, staying destructive and idempotent.
- **15–25 reviews** in the brand voice, **every one backed by a `DELIVERED` order from its author** for that product.
- **4–5 new reviewer-only background customers** are added. These customers, plus existing background customers, get **deterministic, low-priced `DELIVERED` orders** for one inexpensive showcase product. That product carries **12–13 reviews, at least 11 of them by users other than the demo customer**, so "Show more reviews" appears for every viewer.
- Other reviews come from users' existing delivered orders.
- **One seeded review is marked as edited by staff.**
- The demo **customer** gets a **delivered order for the $39 SoulSear Authorization Case** and **no review for it**, so writing a SoulSear review can be demonstrated live. The demo customer also has at least one existing seeded review, so the pinned own-review state can be shown. **DreamWeaver and the Authorization Case are both left unreviewed** for live demonstration.
- The seed adds **no expensive Defense orders**. The extra orders are kept small and cheap so dashboard revenue is barely affected.
- The README's demo notes and the seed's documentation are updated to describe the review demo data.

### Testing

Tests use pytest and pytest-django, follow existing conventions (shared plain fixtures in the project-level conftest, no factory-boy), and **never invoke the seed command**. They cover:

- **Eligibility:**
  - `DELIVERED` qualifies; `PLACED`, `SHIPPED`, and `CANCELLED` each do not
  - signed out is refused
  - already reviewed is refused
  - **next of kin**: a user with no order of their own for the product is refused, even when another user (their relative) has a delivered order for it
  - a verified purchaser can review an **unavailable product** (SoulSear Mark I style)
  - staff without a qualifying purchase cannot create a review
  - the server refuses an ineligible create with 403 and saves nothing
- **Persistence:** a review **survives its order being cancelled**, and its author can still edit and delete it.
- **Model and database:**
  - the unique constraint
  - the rating check constraint rejects 0 and 6
  - comment minimum and maximum enforced by model validation
  - both cascades (deleting a product, deleting a user)
  - order line history unaffected by a product deletion
- **Form:** rating required and in range, comment trimmed, whitespace-only rejected, 9 characters rejected, 10 accepted, 2,000 accepted, 2,001 rejected.
- **Permissions:**
  - authors can edit and delete their own reviews
  - other customers get 404 for the edit form, update, delete confirmation, and delete, and data is unchanged
  - staff can edit and delete any review
- **Edit tracking:**
  - a new review has no "Edited" label
  - a customer edit sets `edited_at` only
  - a staff edit of another user's review sets `edited_by_staff_at`
  - a staff edit of their own review does not
  - an author edit clears `edited_by_staff_at`
- **HTMX responses:**
  - create, edit, cancel, delete confirmation, delete, and cancel delete return the right partials
  - the summary is included as an out-of-band swap
  - invalid input returns 200 with field errors
- **Error handling:**
  - 403 and 404 responses carry the alert, the correct status, and the `HX-Retarget` and `HX-Reswap` headers
  - the `htmx-config` meta tag appears on the product page and not on other pages
  - an anonymous HTMX request gets `HX-Redirect` to sign-in with the right `next`
- **Duplicate races:** a duplicate create caught by the database constraint returns the existing review with a notice, no 500, and exactly one review in the database.
- **Display:**
  - display name for named customers ("Margaret W."), customers without a last name ("Margaret"), and customers without a first name ("Verified customer")
  - public pages never show usernames or emails
  - the "Verified purchase" badge
  - comments are autoescaped
  - the empty state and the summary values
- **Ordering and pagination:**
  - newest first
  - first batch of ten
  - "Show more" returns the next batch and hides itself on the last page
  - the own review is pinned and excluded from batches
  - the highlighted review is pinned below the own review and excluded
  - own and highlighted being the same review
  - wrong-product, deleted, and non-numeric highlight ids are ignored
- **Back office:**
  - staff-only access (anonymous redirected, non-staff 403)
  - newest first, paginated, empty state
  - rows link to the highlighted review on its product page
  - the product delete confirmation shows the review count
- **Slot after delete:** after an author deletes their own review, the form slot shows the form when they still have a delivered order, and the not-eligible message when that order has since been cancelled.

### Definition of done

- The full pytest suite passes.
- Ruff lint and format checks are clean.
- Migrations apply cleanly to the existing database.
- The seed runs twice in a row and produces the agreed review demo data.
- A real browser check confirms:
  - create, edit, and delete happen without a page reload and keep the scroll position
  - "Show more reviews" works
  - HTMX 2 picks up the page-scoped configuration, and the 403/404 alerts actually swap in
  - an expired session redirects to sign-in
- CLAUDE.md and the README describe the new app and its demo data.
- The AI-usage log records the actual development sessions.

## Out of Scope

- **Rating stars or averages on catalog cards.** Catalog cards are unchanged.
- **Sorting or filtering reviews** (highest, lowest, most helpful).
- **Half-star or zero-star ratings**, and any other rating scale.
- **Rating-only reviews** without a comment.
- **Replies, comments on reviews, helpful votes, or reactions.**
- **Photos or attachments** in reviews.
- **Pre-publication moderation or approval queues**, and customer flagging or reporting of reviews.
- **A full edit history** of reviews. Only the "Edited" and "Edited by ThoughtTronix staff" indicators are kept.
- **Soft deletion or undo.** Deletes are permanent.
- **Automatically hiding or deleting reviews** when an order is later cancelled.
- **Linking a review to a specific order line.**
- **Separate back-office edit or delete screens** for reviews. Staff moderate through the inline controls only.
- **Staff writing reviews without a qualifying purchase.**
- **A customer-chosen display name**, and adding first or last name fields to signup or the Security Center.
- **Email notifications** about reviews.
- **A "My reviews" page** in the customer's account.
- **Rate limiting or anti-spam protection** for reviews.
- **Site-wide changes to HTMX error handling**, the django-htmx package, and any JavaScript beyond HTMX attributes and configuration.
- **Expensive Defense orders in the seed**, such as a SoulSear Mark II or a pre-recall Mark I.

## Further Notes

- "Next of kin cannot review" needs no relationship model. Because a review requires the reviewer's own delivered order, everyone who didn't buy and receive the product is already refused: next of kin, gift recipients, and everyone else. An explicit next-of-kin test documents the requirement.
- Showing "Verified customer" instead of a username is deliberate. Signup collects no first name, so a username fallback would have published login usernames for most real customers. The staff-only back-office list may show usernames, because staff need to identify accounts and that page isn't public.
- The page-scoped HTMX configuration means the product page's add-to-cart button would also swap a 404 if one happened. The button is already disabled for unavailable products, so this only arises if a product becomes unavailable while the page is open. It is an accepted edge case.
- Adding the showcase orders slightly raises the dashboard's order count and revenue in the seeded demo world. Tests don't run the seed, so no test should depend on those numbers.
- The defense seed comment's concern still holds: one SoulSear order would flatten every other product on the revenue chart, including the all-time views. That's why the SoulSear review path is shown with the $39 Authorization Case.
- This PRD is the input for the implementation plan, which will be produced separately with `/prd-to-plan`.
