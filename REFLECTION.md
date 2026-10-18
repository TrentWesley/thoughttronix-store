# Reflection

## Product Reviews

### Question 1

One example of TDD in my Product Reviews project was `test_an_author_edit_clears_the_staff_label` in `reviews/test_edit.py`, line 272. This test was created during Phase 3 to make sure that when a customer edits their review after a staff member has edited it, the "Edited by ThoughtTronix staff" label disappears while the regular "Edited" label remains. The test simulates this situation, submits an HTMX request, and checks both the database timestamps and the updated HTML. This was important because the website needed to accurately show who was responsible for changes to a review.

I followed the RED → GREEN TDD process by testing the functionality before implementing it. Initially, 29 of the 30 Phase 3 tests failed because parts of the editing functionality were missing. After implementing the necessary code, all 496 project tests passed. This helped me understand that testing involves more than checking whether a feature works visually. It also requires verifying that the database and application logic behave correctly. I also learned that passing tests do not guarantee every requirement is covered, since the final PRD audit revealed an additional issue with how editing labels were displayed.

### Question 2

One important part of my Product Reviews project was making sure customers could only delete their own reviews, while staff members could delete any review. In `reviews/models.py`, lines 121–129, the `editable_by()` method filters reviews based on the logged-in user. The deletion view in `reviews/views.py`, lines 221–227 and 298–330, uses this method to check authorization before deleting anything. If a customer attempts to delete someone else's review, Django returns a 404 error instead of allowing the deletion.

This was important because simply hiding the Delete button would not provide enough security. Someone could still try to access the deletion URL directly. The test `test_another_customer_gets_404_for_the_delete_and_the_review_stays` in `reviews/test_delete.py`, line 294, verifies that unauthorized attempts fail and the review remains in the database. I learned that authorization needs to be enforced through the application's backend rather than relying only on what users can see on the website.

### Question 3

In my Product Reviews project, I used HTMX to allow customers to submit reviews without refreshing the entire page. In `templates/reviews/partials/_review_form.html`, lines 8–17, the form uses `hx-post` to send the review to Django and `hx-target` to identify which part of the page should update. The request is handled by `CreateReviewView` in `reviews/views.py`, lines 159–194, which checks the customer's eligibility, validates the form, and saves the review.

After the review is saved, Django returns an HTML partial that replaces the form with the customer's new review. The rating summary also updates using `hx-swap-oob` in `templates/reviews/partials/_summary.html`, line 2. This allows both sections to update without reloading the page. The test in `reviews/test_create.py`, lines 208–226, verifies that the review is saved and the updated HTML is returned. This helped me understand how HTMX and Django work together to create a smoother user experience.

### Question 4

One important decision I made during `/grill-me` was deciding who should be allowed to leave product reviews. I chose to only allow customers with a DELIVERED order to post a review instead of allowing anyone who had placed an order. This decision is documented in `PROMPTS.md`, line 514, and `prd/product-reviews.md`, line 24. I chose this option because I wanted reviews to come from customers who had actually received their products.

The tradeoff was that customers would have to wait until their orders were marked as delivered before leaving a review. This also made testing more complicated because test customers needed delivered orders. This decision helped me understand how choosing stricter requirements can improve the reliability of a feature while also adding limitations for users.

## Account Security Center

### Question 1

I chose Phase 5, Password Reset. Users needed to be able to request a reset email, create a new password, and use a link that expires after three days. I tested this in my browser by requesting a reset, opening the email link from the terminal, and changing my password. I confirmed I could sign in with the new password and could not reuse the link. I also checked that unknown emails received the same confirmation message. After correcting a URL I entered incorrectly, everything worked, and all 342 tests passed, so I approved the next phase.

### Question 2

Two Django authentication components used are AuthenticationForm and LoginView.

In accounts/forms.py on line 42:

class SignInForm(AuthenticationForm):

AuthenticationForm validates login credentials while my form adds DaisyUI styling.

In accounts/views.py on line 39:

class SignInView(LoginView):

LoginView handles signing users in and creating authenticated sessions using my custom form and template. This matches the Understanding Authentication lesson because Django handles authentication while my project customizes the forms and appearance.

### Question 3

I chose password reset. In accounts/views.py, my project uses:

class ForgotPasswordView(PasswordResetView):

class ResetPasswordView(PasswordResetConfirmView):

PasswordResetView handles reset requests, while PasswordResetConfirmView validates reset links and allows users to create new passwords. The project also uses PasswordResetDoneView and PasswordResetCompleteView for confirmation pages.

This matches the Password Management lesson because Django handles password validation and reset tokens instead of using custom security code. My project uses the console email backend in config/settings.py to display reset links in the terminal, just like the lesson explains. I kept the custom styling and security notifications because they were required by the project. I tested the complete reset process in my browser before approving Phase 5.

### Question 4

Phase 5 was a useful stopping point because the entire password reset process worked before moving forward. I could request an email, reset my password, sign in, and confirm the old link was invalid. Testing a complete feature made it easier to catch problems and approve the phase before starting Phase 6.

## Product Images

### Question 1
During /grill-me, Claude recommended having the seed command automatically attach the provided images to products. I decided not to do that because I wanted the seed data to stay unchanged and upload the images myself through the back office. We discussed the options and I chose to keep the product-images folder temporary and uncommitted. This also allowed me to test the actual image upload process myself.

### Question 2
The product image field is in products/models.py on lines 84-93:

image = ProductImageField(
    upload_to="products/",
    max_length=255,
    blank=True,
    validators=[validate_product_image],
    help_text=(
        "Optional. A JPEG, PNG, or WebP image, up to 5 MB and at least "
        "600 pixels on its shortest side."
    ),
)

The upload_to="products/" value is on line 85. The field uses ProductImageField, which is a subclass of Django's ImageField. The upload_to setting tells Django to store product images inside the products folder in the media directory.

The opening form tag is in templates/products/manage_product_form.html on line 13:

<form method="post" enctype="multipart/form-data" class="mt-2 space-y-4">

The enctype="multipart/form-data" is needed so the browser can send the uploaded image file with the rest of the form data.

### Question 3
For my FocusForge product, the database stores products/focusforge-c4641c.webp. The actual image file is stored at media/products/focusforge-c4641c.webp, and the browser accesses it at /media/products/focusforge-c4641c.webp. MEDIA_ROOT in config/settings.py on line 145 controls where the uploaded file is stored, while MEDIA_URL on line 143 provides the /media/ part of the browser URL. The image field stores the relative path in the database, and the image_url property in products/models.py on lines 135-140 returns the uploaded image URL. In development, config/urls.py on lines 22-23 uses Django's static() helper when DEBUG is on so the browser can access uploaded files from MEDIA_ROOT.

## Discount Coupons

### Question 1
Claude recommended having a seeded discounted order so historical coupon behavior was already represented. I decided not to do that because I preferred to create a discounted order myself during browser testing. After creating the order with a coupon, I retired the coupon and checked that the existing order still kept its original discount. This let the seed data provide examples of live, expired, and retired coupons without creating a fake discounted order.

### Question 2
When adding coupons and creating codes, there was a section for choosing which products the coupon would apply to. During my initial browser check, I noticed that this section was extremely messy because the product names were overlapping. I went back into Claude and had it fix the product selector by changing it to simple checkboxes that did not overlap. After making the change, I checked it again in the browser and found that the products were much easier to read and select. No existing tests failed, and after the change, all 232 tests passed.

## Featured Products

### Question 1

I checked Is featured on the admin page, which changes the product's is_featured value in products/models.py. The templates/products/catalog.html and templates/products/detail.html files check that value, and when it is true, they show the Featured badge.

### Question 2

To verify that the feature worked, I visited the catalog page and saw the Featured badges. Then I clicked on Seraphine and saw the Featured badge on its product detail page. Finally, I ran uv run pytest and all 166 tests passed.

### Question 3
One problem I ran into was when I opened Seraphine and SoulSear Mark II, the Is available box was checked, but for SoulSear Mark I it was unchecked. I was debating whether to check it so they would all be the same, but after looking into it, I decided to leave it unchecked and only change the Is featured setting.