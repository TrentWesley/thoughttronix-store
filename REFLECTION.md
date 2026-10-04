# Reflection

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