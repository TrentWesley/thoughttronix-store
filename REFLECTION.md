# Reflection
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