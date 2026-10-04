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
